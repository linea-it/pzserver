"""Device login, safe persistence and refresh through the public package API."""

import json
import stat
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from pzserver import PzServer, login_device, logout
from pzserver import device_auth as device


def tokens(access="access", refresh="refresh", expires=3600):
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "expires_in": expires,
    }


def save(host="localhost", expires=3600):
    with device._lock(host):
        device._save(
            host,
            device._credentials(
                device._endpoint(host), tokens(expires=expires), device.time.time()
            ),
        )


@pytest.fixture
def wire(monkeypatch):
    post = Mock()
    monkeypatch.setattr(device.requests, "post", post)
    monkeypatch.setattr(device.time, "sleep", Mock())
    monkeypatch.setattr(device, "_open_browser", Mock())
    return post


def response(payload, status=200):
    return Mock(status_code=status, json=Mock(return_value=payload))


def start():
    return {
        "verification_uri": "http://localhost/api/device-oauth/device/",
        "user_code": "ABCD-EFGH",
        "device_code": "secret-device",
        "expires_in": 600,
        "interval": 5,
        "user_code_max_attempts": 3,
    }


def test_browser_login_pending_slowdown_persistence_and_reuse(
    wire, monkeypatch, capsys
):
    wire.side_effect = [
        response(start()),
        response({"error": "authorization_pending"}, 400),
        response({"error": "slow_down"}, 400),
        response(tokens()),
    ]
    login_device(host="localhost")
    assert [call.args[0] for call in device.time.sleep.call_args_list] == [5, 5, 10]
    assert (
        device._path("localhost").stat().st_mode & 0o777 == stat.S_IRUSR | stat.S_IWUSR
    )
    assert device._path("localhost").parent.stat().st_mode & 0o777 == 0o700
    output = capsys.readouterr().out
    assert "ABCD-EFGH" in output
    assert "secret-device" not in output and "refresh" not in output
    monkeypatch.setattr(device.PzRequests, "_check_token", Mock())
    assert PzServer(host="localhost").api._authorization == "Bearer access"
    assert PzServer(host="localhost").api._authorization == "Bearer access"
    assert wire.call_count == 4
    for call in wire.call_args_list:
        assert call.kwargs["allow_redirects"] is False
        assert call.kwargs["timeout"] == (5, 30)


def test_refresh_rotation_serialized_across_instances(wire):
    save(expires=1)
    wire.return_value = response(tokens("new-access", "new-refresh"))
    with ThreadPoolExecutor(max_workers=3) as pool:
        actual = list(
            pool.map(
                lambda _: device.DeviceCredentials("localhost").access_token(), range(3)
            )
        )
    assert actual == ["new-access"] * 3
    wire.assert_called_once()
    assert (
        json.loads(device._path("localhost").read_text())["refresh_token"]
        == "new-refresh"
    )


def test_existing_instance_renews_before_request(wire, monkeypatch):
    save()
    monkeypatch.setattr(device.PzRequests, "_check_token", Mock())
    api = PzServer(host="localhost").api
    assert api._authorization == "Bearer access"
    save(expires=1)
    wire.return_value = response(tokens("renewed", "rotated"))
    assert api._authorization == "Bearer renewed"


@pytest.mark.parametrize("error", ["access_denied", "expired_token", "invalid_grant"])
def test_failure_preserves_existing_credentials(wire, error):
    save()
    before = device._path("localhost").read_bytes()
    wire.side_effect = [response(start()), response({"error": error}, 400)]
    with pytest.raises(device.DeviceAuthError):
        login_device(host="localhost", open_browser=False, force=True)
    assert device._path("localhost").read_bytes() == before


def test_revoked_refresh_fails_without_manual_or_hub_fallback(wire, monkeypatch):
    save(expires=1)
    wire.return_value = response({"error": "invalid_grant"}, 400)
    with pytest.raises(device.DeviceAuthError, match="renew"):
        PzServer(host="localhost", auto_login=False)


def test_endpoint_isolation_explicit_override_and_logout(wire, monkeypatch):
    save()
    monkeypatch.setattr(device.PzRequests, "_check_token", Mock())
    assert device.load_device_credentials("pz-dev") is None
    assert (
        PzServer(token="manual", host="localhost").api._authorization == "Token manual"
    )
    logout(host="localhost")
    assert device.load_device_credentials("localhost") is None
    wire.assert_not_called()


@pytest.mark.parametrize(
    "url",
    [
        "http://other.example/api",
        "https://user:secret@host/api",
        "https://host/api?query=1",
    ],
)
def test_insecure_endpoints_rejected_without_network(wire, url):
    with pytest.raises(ValueError):
        login_device(host=url)
    wire.assert_not_called()


def test_cross_origin_verification_rejected(wire):
    wire.return_value = response(
        {**start(), "verification_uri": "https://other.example/device"}
    )
    with pytest.raises(device.DeviceAuthError):
        login_device(host="localhost")
    device._open_browser.assert_not_called()


def test_redirect_token_response_rejected(wire):
    save(expires=1)
    wire.return_value = response(tokens(), 302)
    with pytest.raises(device.DeviceAuthError):
        device.DeviceCredentials("localhost").access_token()


def test_login_reuses_saved_authorization_without_browser(wire, capsys):
    save()
    wire.return_value = response(tokens("renewed", "rotated"))
    assert login_device(host="localhost") is None
    assert wire.call_count == 1
    assert wire.call_args.args[0].endswith("/token/")
    assert wire.call_args.kwargs["data"]["grant_type"] == "refresh_token"
    assert device._read("localhost")["refresh_token"] == "rotated"
    device._open_browser.assert_not_called()
    assert "no browser login needed" in capsys.readouterr().out


def test_force_login_creates_new_authorization(wire):
    save()
    wire.side_effect = [response(start()), response(tokens("new", "new-refresh"))]
    login_device(host="localhost", force=True)
    assert wire.call_args_list[0].args[0].endswith("/device-authorization/")
    assert device._read("localhost")["access_token"] == "new"
    device._open_browser.assert_called_once()


def test_revoked_saved_login_requests_new_approval(wire):
    save()
    wire.side_effect = [
        response({"error": "invalid_grant"}, 400),
        response(start()),
        response(tokens("new", "new-refresh")),
    ]
    login_device(host="localhost")
    assert device._read("localhost")["access_token"] == "new"
    device._open_browser.assert_called_once()


@pytest.mark.parametrize(
    "status,error",
    [(500, "server_error"), (429, "rate_limit"), (400, "invalid_client")],
)
def test_login_server_failure_does_not_create_authorization(wire, status, error):
    save()
    before = device._path("localhost").read_bytes()
    wire.return_value = response({"error": error}, status)
    with pytest.raises(device.DeviceAuthError):
        login_device(host="localhost")
    assert device._path("localhost").read_bytes() == before
    wire.assert_called_once()
    device._open_browser.assert_not_called()


def test_login_network_failure_does_not_create_authorization(wire):
    save()
    before = device._path("localhost").read_bytes()
    wire.side_effect = device.requests.Timeout()
    with pytest.raises(device.DeviceAuthError):
        login_device(host="localhost")
    assert device._path("localhost").read_bytes() == before
    wire.assert_called_once()
    device._open_browser.assert_not_called()


def test_constructor_starts_login_when_no_credentials(wire, monkeypatch, capsys):
    wire.side_effect = [response(start()), response(tokens())]
    monkeypatch.setattr(device.PzRequests, "_check_token", Mock())
    server = PzServer(host="localhost", open_browser=False)
    assert server.api._authorization == "Bearer access"
    assert "Enter code:" in capsys.readouterr().out
    device._open_browser.assert_not_called()


def test_constructor_reauthorizes_revoked_refresh(wire, monkeypatch):
    save(expires=1)
    wire.side_effect = [
        response({"error": "invalid_grant"}, 400),
        response({"error": "invalid_grant"}, 400),
        response(start()),
        response(tokens("new-access", "new-refresh")),
    ]
    monkeypatch.setattr(
        device.PzRequests,
        "_get_request",
        lambda api, url: {"success": bool(api._authorization)},
    )
    server = PzServer(host="localhost", open_browser=False)
    assert server.api._authorization == "Bearer new-access"


def test_constructor_recovers_401_without_new_authorization_if_refresh_valid(
    wire, monkeypatch
):
    save()
    wire.return_value = response(tokens("renewed", "rotated"))
    monkeypatch.setattr(
        device.PzRequests,
        "_get_request",
        Mock(
            side_effect=[
                {"success": False, "status_code": 401},
                {"success": True},
            ]
        ),
    )
    server = PzServer(host="localhost")
    assert server.api._authorization == "Bearer renewed"
    assert wire.call_count == 1
    device._open_browser.assert_not_called()


@pytest.mark.parametrize("status", [403, 429, 500, 504])
def test_constructor_server_errors_do_not_launch_login(wire, monkeypatch, status):
    save()
    monkeypatch.setattr(
        device.PzRequests,
        "_get_request",
        Mock(return_value={"success": False, "status_code": status}),
    )
    with pytest.raises(device.requests.RequestException):
        PzServer(host="localhost")
    wire.assert_not_called()
    device._open_browser.assert_not_called()


def test_constructor_explicit_invalid_token_does_not_switch_identity(wire, monkeypatch):
    monkeypatch.setattr(
        device.PzRequests,
        "_get_request",
        Mock(return_value={"success": False, "status_code": 401}),
    )
    with pytest.raises(device.requests.RequestException):
        PzServer(token="explicit", host="localhost")
    wire.assert_not_called()


def test_constructor_saved_manual_401_can_start_device_login(wire, monkeypatch):
    from pzserver import auth

    path = auth._token_path("localhost")
    path.parent.mkdir(parents=True)
    path.write_text("old-manual")
    monkeypatch.setattr(
        device.PzRequests,
        "_get_request",
        Mock(
            side_effect=[
                {"success": False, "status_code": 401},
                {"success": True},
            ]
        ),
    )
    wire.side_effect = [response(start()), response(tokens())]
    assert PzServer(host="localhost").api._authorization == "Bearer access"


def test_constructor_noninteractive_mode_never_starts_login(wire):
    with pytest.raises(ValueError, match="login_device"):
        PzServer(host="localhost", auto_login=False)
    wire.assert_not_called()


def test_interrupted_login_resumes_same_code_without_new_issue(wire, capsys):
    wire.side_effect = [response(start()), KeyboardInterrupt()]
    with pytest.raises(KeyboardInterrupt):
        login_device(host="localhost", open_browser=False)
    pending = device._read_pending("localhost")
    expiry = pending["expires_at"]
    assert device._pending_path("localhost").stat().st_mode & 0o777 == 0o600
    wire.reset_mock()
    wire.side_effect = [response(tokens())]
    login_device(host="localhost", open_browser=False)
    wire.assert_called_once()
    assert wire.call_args.kwargs["data"]["device_code"] == pending["device_code"]
    assert expiry > device.time.time()
    assert device._read_pending("localhost") is None
    assert "Resuming pending" in capsys.readouterr().out


def test_forced_restart_cancels_pending_before_new_issue(wire):
    wire.side_effect = [response(start()), KeyboardInterrupt()]
    with pytest.raises(KeyboardInterrupt):
        login_device(host="localhost", open_browser=False)
    wire.reset_mock()
    wire.side_effect = [
        response({"cancelled": True}),
        response(start()),
        response(tokens()),
    ]
    login_device(host="localhost", force=True, open_browser=False)
    assert [c.args[0].split("/")[-2] for c in wire.call_args_list] == [
        "cancel",
        "device-authorization",
        "token",
    ]
    assert device._read_pending("localhost") is None


def test_cancellation_failure_keeps_pending_and_does_not_issue(wire):
    wire.side_effect = [response(start()), KeyboardInterrupt()]
    with pytest.raises(KeyboardInterrupt):
        login_device(host="localhost", open_browser=False)
    before = device._pending_path("localhost").read_bytes()
    wire.reset_mock()
    wire.side_effect = [response({"error": "server_error"}, 500)]
    with pytest.raises(device.DeviceAuthError):
        login_device(host="localhost", force=True)
    wire.assert_called_once()
    assert device._pending_path("localhost").read_bytes() == before


def test_expired_pending_request_is_replaced_without_extending_original(wire):
    wire.side_effect = [response(start()), KeyboardInterrupt()]
    with pytest.raises(KeyboardInterrupt):
        login_device(host="localhost", open_browser=False)
    pending = device._read_pending("localhost")
    device._write_json(
        device._pending_path("localhost"),
        {**pending, "expires_at": device.time.time() - 1},
    )
    wire.reset_mock()
    wire.side_effect = [response(start()), response(tokens())]
    login_device(host="localhost", open_browser=False)
    assert wire.call_args_list[0].args[0].endswith("/device-authorization/")


def test_denial_or_three_errors_clears_pending_state(wire):
    wire.side_effect = [response(start()), response({"error": "access_denied"}, 400)]
    with pytest.raises(device.DeviceAuthError, match="blocked"):
        login_device(host="localhost", open_browser=False)
    assert device._read_pending("localhost") is None


def test_resuming_keeps_slow_down_interval(wire):
    wire.side_effect = [
        response(start()),
        response({"error": "slow_down"}, 400),
        KeyboardInterrupt(),
    ]
    with pytest.raises(KeyboardInterrupt):
        login_device(host="localhost", open_browser=False)
    assert device._read_pending("localhost")["interval"] == 10
    wire.reset_mock()
    device.time.sleep.reset_mock()
    wire.side_effect = [response(tokens())]
    login_device(host="localhost", open_browser=False)
    assert device.time.sleep.call_args.args[0] >= 10


def test_forced_constructor_ignores_saved_authorization(wire, monkeypatch):
    save()
    monkeypatch.setattr(device.PzRequests, "_check_token", Mock())
    wire.side_effect = [response(start()), response(tokens("new", "rotated"))]
    server = PzServer(host="localhost", force=True, open_browser=False)
    assert server.api._authorization == "Bearer new"
    assert wire.call_args_list[0].args[0].endswith("/device-authorization/")
    device._open_browser.assert_not_called()


def test_forced_constructor_cancels_pending_request(wire, monkeypatch):
    wire.side_effect = [response(start()), KeyboardInterrupt()]
    with pytest.raises(KeyboardInterrupt):
        login_device(host="localhost", open_browser=False)
    wire.reset_mock()
    wire.side_effect = [
        response({"cancelled": True}),
        response(start()),
        response(tokens()),
    ]
    monkeypatch.setattr(device.PzRequests, "_check_token", Mock())
    server = PzServer(host="localhost", force=True, open_browser=False)
    assert server.api._authorization == "Bearer access"
    assert wire.call_args_list[0].args[0].endswith("/cancel/")


@pytest.mark.parametrize(
    "kwargs",
    [{"token": "explicit"}, {"hub": "https://hub.example"}, {"auto_login": False}],
)
def test_forced_constructor_rejects_conflicting_options(wire, kwargs):
    with pytest.raises(ValueError, match="force=True"):
        PzServer(host="localhost", force=True, **kwargs)
    wire.assert_not_called()


def test_browser_launcher_isolated_without_shell(monkeypatch):
    run = Mock()
    monkeypatch.setattr(device.subprocess, "run", run)
    url = "http://localhost/api/device-oauth/device/?request=test&other=value"
    device._open_browser(url)
    args, kwargs = run.call_args
    assert args[0][-1] == url
    assert args[0][0] == device.sys.executable
    assert kwargs["stderr"] == device.subprocess.DEVNULL
    assert kwargs["stdout"] == device.subprocess.DEVNULL
    assert kwargs.get("shell", False) is False
    assert kwargs["timeout"] == 5


@pytest.mark.parametrize(
    "error",
    [OSError("missing launcher"), device.subprocess.TimeoutExpired("launcher", 5)],
)
def test_browser_launch_failure_does_not_interrupt_login(monkeypatch, error):
    monkeypatch.setattr(device.subprocess, "run", Mock(side_effect=error))
    device._open_browser("http://localhost")


def test_browser_child_errors_are_silenced(monkeypatch, tmp_path, capfd):
    launcher = tmp_path / "launcher.py"
    launcher.write_text(
        "import sys; print('gio: Failed to find default application', file=sys.stderr)"
    )
    monkeypatch.setenv("BROWSER", f'"{device.sys.executable}" "{launcher}" %s')
    device._open_browser("http://localhost")
    assert capfd.readouterr().err == ""


def test_login_always_prints_manual_instructions(wire, capsys):
    wire.side_effect = [response(start()), response(tokens())]
    login_device(host="localhost")
    output = capsys.readouterr().out
    assert "If it does not open" in output
    assert start()["verification_uri"] in output
    assert start()["user_code"] in output
    assert "Sign in" in output and "Authorize access" in output
    assert "Keep this Python session running" in output
    assert start()["device_code"] not in output


def test_login_prints_server_configured_code_attempt_limit(wire, capsys):
    authorization = {**start(), "user_code_max_attempts": 7}
    wire.side_effect = [response(authorization), response(tokens())]
    login_device(host="localhost", open_browser=False)
    assert "7 incorrect code entries" in capsys.readouterr().out


@pytest.mark.parametrize("attempts", [None, True, 0, -1, 1.5, "3"])
def test_invalid_code_attempt_policy_is_rejected(wire, attempts):
    authorization = {**start(), "user_code_max_attempts": attempts}
    wire.return_value = response(authorization)
    with pytest.raises(device.DeviceAuthError, match="Invalid device authorization"):
        login_device(host="localhost", open_browser=False)
