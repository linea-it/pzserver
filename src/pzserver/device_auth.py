"""Browser authorization and renewable, endpoint-bound OAuth credentials."""

import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests
from filelock import FileLock
from filelock import Timeout as LockTimeout

from .auth import _token_path
from .communicate import PzRequests

CLIENT_ID = "pzserver-python-device"
REQUEST_TIMEOUT = (5, 30)
BROWSER_LAUNCH_TIMEOUT = 5
CREDENTIAL_LOCK_TIMEOUT = 40
REFRESH_EARLY_SECONDS = 60
SLOW_DOWN_INCREMENT_SECONDS = 5


class DeviceAuthError(RuntimeError):
    """Authorization failed; secrets are never included in the error message."""


class DeviceLoginRequired(DeviceAuthError):
    """The server rejected an expired or revoked refresh token."""


def _endpoint(host):
    url = PzRequests._enviroments.get(host, host).rstrip("/")
    parsed = urlsplit(url)
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or "\\" in url
        or any(c.isspace() for c in url)
        or not (
            parsed.scheme == "https"
            or (
                parsed.scheme == "http"
                and parsed.hostname in ("localhost", "127.0.0.1", "::1")
            )
        )
    ):
        raise ValueError("OAuth requires HTTPS (HTTP is allowed only on loopback).")
    return url


def _path(host):
    return _token_path(host).with_suffix(".oauth.json")


def _lock(host):
    path = _path(host)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    return FileLock(str(path) + ".lock", timeout=CREDENTIAL_LOCK_TIMEOUT, mode=0o600)


def _read(host):
    try:
        return json.loads(_path(host).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (ValueError, OSError) as error:
        raise DeviceAuthError(
            "Cannot read OAuth credentials; run login_device again."
        ) from error


def _save(host, data):
    _write_json(_path(host), data)


def _write_json(path, data):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _post(endpoint, path, data):
    try:
        response = requests.post(
            endpoint + "/device-oauth/" + path,
            data=data,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise DeviceAuthError(
            "Could not contact the authorization server; try again."
        ) from None
    try:
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError
    except ValueError:
        raise DeviceAuthError("Invalid authorization server response.") from None
    if 300 <= response.status_code < 400 or response.status_code >= 500:
        raise DeviceAuthError(
            f"Authorization server returned HTTP {response.status_code}."
        )
    return response.status_code, payload


def _credentials(endpoint, data, requested_at):
    try:
        expires = float(data["expires_in"])
        if not math.isfinite(expires) or expires <= 0:
            raise ValueError
        if data["token_type"].lower() != "bearer":
            raise ValueError
        for key in ("access_token", "refresh_token"):
            if (
                not isinstance(data[key], str)
                or not data[key]
                or any(c.isspace() for c in data[key])
            ):
                raise ValueError
        return {
            "endpoint": endpoint,
            "client_id": CLIENT_ID,
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": requested_at + expires,
        }
    except (KeyError, TypeError, ValueError, AttributeError):
        raise DeviceAuthError("Invalid OAuth token response.") from None


def _open_browser(url):
    """Isolate launcher output, including errors emitted by its child processes."""
    try:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys, webbrowser; webbrowser.open(sys.argv[1])",
                url,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=BROWSER_LAUNCH_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        # Browser launch is optional; the printed instructions remain usable.
        pass


def _pending_path(host):
    return _path(host).with_suffix(".pending.json")


def _read_pending(host):
    try:
        data = json.loads(_pending_path(host).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("endpoint") != _endpoint(host):
            raise ValueError
        if not isinstance(data.get("expires_at"), (int, float)) or not math.isfinite(
            data["expires_at"]
        ):
            raise ValueError
        return data
    except FileNotFoundError:
        return None
    except (ValueError, TypeError, OSError):
        raise DeviceAuthError("Cannot read the pending authorization file.") from None


def _clear_pending(host):
    _pending_path(host).unlink(missing_ok=True)


def login_device(host="pz", *, open_browser=True, force=False):
    """Reuse saved authorization or resume its pending browser approval.

    force=True cancels an unredeemed pending code before requesting a new one.
    Previously issued authorizations are not revoked by force=True.
    An interrupted login keeps its private pending state without extending expiry.
    """
    _endpoint(host)
    with _lock(host):
        pass  # Ensure the private credential directory exists.
    lock = FileLock(str(_pending_path(host)) + ".lock", timeout=0, mode=0o600)
    try:
        with lock:
            return _login_device(host, open_browser=open_browser, force=force)
    except LockTimeout:
        raise DeviceAuthError(
            "Login is already running for this API. Use its displayed code or interrupt it before restarting."
        ) from None


def _login_device(host, *, open_browser, force):
    endpoint = _endpoint(host)
    pending = _read_pending(host)
    if pending and pending["expires_at"] <= time.time():
        _clear_pending(host)
        pending = None
    if pending and force:
        status, _ = _post(
            endpoint,
            "cancel/",
            {
                "client_id": CLIENT_ID,
                "device_code": pending["device_code"],
            },
        )
        if status != 200:
            raise DeviceAuthError(
                "Could not cancel the pending request; no new code was issued."
            )
        _clear_pending(host)
        pending = None
    if not force and pending is None:
        saved = load_device_credentials(host)
        if saved is not None:
            try:
                saved.access_token(force_refresh=True)
            except DeviceLoginRequired:
                # Keep the old file until the new authorization succeeds.
                pass
            else:
                print(
                    "Existing PzServer authorization renewed; no browser login needed."
                )
                return
    requested_at = time.time()
    if pending is None:
        status, data = _post(
            endpoint,
            "device-authorization/",
            {
                "client_id": CLIENT_ID,
                "scope": "read write",
            },
        )
        if status != 200:
            raise DeviceAuthError(
                "Could not start Device Flow; check whether it is enabled or rate limited."
            )
    else:
        data = {**pending, "expires_in": pending["expires_at"] - requested_at}
    try:
        verification = data["verification_uri"]
        # Do not open arbitrary destinations supplied by an unexpected response.
        if (
            urlsplit(verification).netloc != urlsplit(endpoint).netloc
            or urlsplit(verification).scheme != urlsplit(endpoint).scheme
        ):
            raise ValueError
        code = data["user_code"]
        device = data["device_code"]
        lifetime = float(data["expires_in"])
        interval = max(1, float(data.get("interval", 5)))
        max_code_attempts = data["user_code_max_attempts"]
        if (
            not all(isinstance(v, str) and v for v in (code, device))
            or not all(math.isfinite(v) and v > 0 for v in (lifetime, interval))
            or type(max_code_attempts) is not int
            or max_code_attempts <= 0
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise DeviceAuthError("Invalid device authorization response.") from None
    if pending is None:
        pending = {
            **data,
            "endpoint": endpoint,
            "expires_at": requested_at + lifetime,
            "next_poll_at": time.time() + interval,
        }
        _write_json(_pending_path(host), pending)
    else:
        print("Resuming pending authorization (the expiration time is unchanged).")
    remaining_minutes = max(1, math.ceil((pending["expires_at"] - time.time()) / 60))
    browser_instruction = (
        "We will try to open your browser automatically. "
        "If it does not open, copy the complete link below and open it manually."
        if open_browser
        else "Open your browser manually and paste the complete link below."
    )
    print(
        "\nAuthorize this Python environment to access PzServer.\n"
        f"{browser_instruction}\n\n"
        f"1. Open this link (including everything after '?'):\n   {verification}\n"
        "2. Sign in to your PzServer account if requested.\n"
        f"3. Enter code: {code}\n"
        "4. Review the request and select 'Authorize access'.\n\n"
        f"You have about {remaining_minutes} minute(s) remaining. "
        f"{max_code_attempts} incorrect code entries block this request.\n"
        "Keep this Python session running while you authorize in the browser.\n"
        "Waiting for your approval…",
        flush=True,
    )
    if open_browser:
        _open_browser(verification)
    deadline = time.monotonic() + max(0, pending["expires_at"] - time.time())
    while time.monotonic() < deadline:
        delay = max(interval, pending.get("next_poll_at", 0) - time.time())
        if time.monotonic() + delay >= deadline:
            break
        time.sleep(delay)
        pending["next_poll_at"] = time.time() + interval
        _write_json(_pending_path(host), pending)
        requested_at = time.time()
        status, tokens = _post(
            endpoint,
            "token/",
            {
                "client_id": CLIENT_ID,
                "device_code": device,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        if status == 200:
            credentials = _credentials(endpoint, tokens, requested_at)
            with _lock(host):
                _save(host, credentials)
            _clear_pending(host)
            return
        error = tokens.get("error")
        if error == "authorization_pending":
            continue
        if status == 429:
            raise DeviceAuthError(
                "Authorization requests are rate limited. Wait before resuming login."
            )
        if error == "slow_down":
            interval += SLOW_DOWN_INCREMENT_SECONDS
            pending["interval"] = interval
            pending["next_poll_at"] = time.time() + interval
            _write_json(_pending_path(host), pending)
            continue
        if error == "access_denied":
            _clear_pending(host)
            raise DeviceAuthError(
                "Authorization denied, cancelled or blocked. Restart login to obtain a new code."
            )
        if error == "expired_token":
            break
        if error == "invalid_grant":
            _clear_pending(host)
        raise DeviceAuthError("Device authorization failed; run login_device again.")
    _clear_pending(host)
    raise DeviceAuthError("Authorization expired; run login_device again.")


class DeviceCredentials:
    """Reload and serialize refresh across notebook processes and instances."""

    def __init__(self, host):
        self.host = host
        self.endpoint = _endpoint(host)

    def access_token(self, *, force_refresh=False):
        with _lock(self.host):
            saved = _read(self.host)
            if not saved:
                raise DeviceAuthError("No OAuth credentials; run login_device again.")
            if (
                saved.get("endpoint") != self.endpoint
                or saved.get("client_id") != CLIENT_ID
            ):
                raise DeviceAuthError("OAuth credentials do not match this API.")
            if (
                not force_refresh
                and saved.get("expires_at", 0) > time.time() + REFRESH_EARLY_SECONDS
            ):
                return saved["access_token"]
            requested_at = time.time()
            status, tokens = _post(
                self.endpoint,
                "token/",
                {
                    "client_id": CLIENT_ID,
                    "grant_type": "refresh_token",
                    "refresh_token": saved["refresh_token"],
                },
            )
            if status == 400 and tokens.get("error") == "invalid_grant":
                raise DeviceLoginRequired(
                    "Could not renew login: authorization expired or was revoked. "
                    "Run login_device again."
                )
            if status != 200:
                raise DeviceAuthError(
                    "Could not renew login; run login_device again if it expired or was revoked."
                )
            renewed = _credentials(self.endpoint, tokens, requested_at)
            _save(self.host, renewed)
            return renewed["access_token"]


def load_device_credentials(host):
    if not _path(host).exists():
        return None
    return DeviceCredentials(host)


def forget_device_credentials(host):
    if _path(host).exists():
        with _lock(host):
            _path(host).unlink(missing_ok=True)
