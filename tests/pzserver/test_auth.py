"""Credential persistence, isolation, and validation tests."""

import os
import stat
from unittest.mock import Mock

import pytest
import requests

from pzserver import PzServer, auth, core, login, logout


@pytest.fixture
def validate(monkeypatch):
    validator = Mock()
    monkeypatch.setattr(auth.PzRequests, "_check_token", validator)
    return validator


def test_login_prompts_and_new_instances_reuse_token(monkeypatch, validate):
    prompt = Mock(return_value="secret")
    monkeypatch.setattr(auth.getpass, "getpass", prompt)

    assert login() is None
    assert PzServer().api._token == "secret"
    assert PzServer().api._token == "secret"
    prompt.assert_called_once()
    assert auth.load_token() == "secret"


def test_tokens_are_isolated_by_endpoint(validate):
    login("production")
    login("development", host="pz-dev")

    assert PzServer().api._token == "production"
    assert PzServer(host="pz-dev").api._token == "development"
    assert auth.load_token("https://pzserver.linea.org.br/api/") == "production"
    with pytest.raises(ValueError, match="pzserver.login"):
        PzServer(host="https://another.example/api/")


def test_explicit_token_does_not_read_or_replace_saved_token(monkeypatch, validate):
    login("saved")
    monkeypatch.setattr(core, "load_token", Mock(side_effect=AssertionError))
    assert PzServer(token="explicit").api._token == "explicit"
    assert auth.load_token() == "saved"


def test_validation_failure_preserves_previous_credential(validate):
    login("saved")
    validate.side_effect = requests.exceptions.RequestException("Unauthorized")
    with pytest.raises(requests.exceptions.RequestException):
        login("invalid")
    assert auth.load_token() == "saved"
    with pytest.raises(requests.exceptions.RequestException):
        login("invalid", host="pz-dev")
    assert auth.load_token("pz-dev") is None


def test_logout_only_removes_selected_host(validate):
    login("production")
    login("development", host="pz-dev")
    logout()
    logout()
    assert auth.load_token() is None
    assert auth.load_token("pz-dev") == "development"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions")
def test_private_permissions_including_replacement(validate):
    login("first")
    path = auth._token_path("pz")
    path.chmod(0o644)
    login("replacement")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert list(path.parent.iterdir()) == [path]


def test_failed_write_preserves_old_token_and_cleans_temporary(monkeypatch, validate):
    login("saved")
    monkeypatch.setattr(auth.os, "replace", Mock(side_effect=OSError("disk error")))
    with pytest.raises(OSError):
        login("replacement")
    path = auth._token_path("pz")
    assert auth.load_token() == "saved"
    assert list(path.parent.iterdir()) == [path]


def test_empty_token_is_not_saved(validate):
    with pytest.raises(ValueError, match="valid token"):
        login("  ")
    validate.assert_not_called()
    assert auth.load_token() is None


def test_partner_discovery_and_request_header(monkeypatch, validate):
    monkeypatch.setenv("JUPYTERHUB_PUBLIC_HUB_URL", "https://jupyter-dev.linea.org.br/hub/")
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", "hub-secret")
    api = PzServer(host="pz-dev").api
    send = Mock(return_value={})
    monkeypatch.setattr(api, "_send_request", send)
    api._get_request("https://pzserver-dev.linea.org.br/api/")
    request = send.call_args.args[0]
    assert request.headers["Authorization"] == "JupyterHub linea-dev hub-secret"
    assert auth.load_token("pz-dev") is None


def test_partner_does_not_receive_local_or_explicit_token_priority(monkeypatch, validate):
    monkeypatch.setenv("JUPYTERHUB_PUBLIC_HUB_URL", "https://jupyter-dev.linea.org.br/")
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", "hub-secret")
    login("saved")
    assert PzServer().api._authorization == "Token saved"
    assert PzServer(token="explicit").api._authorization == "Token explicit"
    assert PzServer(hub="linea-dev").api._authorization == "JupyterHub linea-dev hub-secret"


def test_partner_token_is_never_discovered_for_arbitrary_destination(monkeypatch):
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", "hub-secret")
    monkeypatch.setenv("JUPYTERHUB_PUBLIC_HUB_URL", "https://jupyter-dev.linea.org.br/")
    assert auth.hub_credentials("https://another.example/api/") is None
    with pytest.raises(ValueError, match="trusted"):
        auth.hub_credentials("https://another.example/api/", hub="linea-dev")


def test_unknown_hub_is_not_automatically_used(monkeypatch):
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", "hub-secret")
    monkeypatch.setenv("JUPYTERHUB_PUBLIC_HUB_URL", "https://nb.data.lsst.cloud/nb/hub/")
    assert auth.hub_credentials() is None
    with pytest.raises(ValueError, match="Unknown"):
        auth.hub_credentials(hub="rubin")
