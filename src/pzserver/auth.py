"""Persist user-provided API tokens separately for each API endpoint."""

import getpass
import hashlib
import os
import tempfile
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from .communicate import PzRequests

TRUSTED_PZSERVER_APIS = {
    "https://pzserver.linea.org.br/api",
    "https://pzserver-dev.linea.org.br/api",
}


def normalize_hub_url(value):
    """Normalize HTTPS origin and trailing slashes; preserve the path prefix."""
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError("Invalid Hub URL.")
    if any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("Invalid Hub URL.")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or "?" in value
        or "#" in value
        or "%" in parsed.netloc
        or "%" in parsed.path
        or any(part in (".", "..") for part in parsed.path.split("/"))
    ):
        raise ValueError("Invalid Hub URL.")
    port = parsed.port
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    authority = host if port in (None, 443) else f"{host}:{port}"
    return f"https://{authority}{parsed.path.rstrip('/')}"


def hub_credentials(host="pz", hub=None):
    """Discover partner credentials, only for known PzServer destinations."""
    endpoint = PzRequests._enviroments.get(host, host).rstrip("/")
    if endpoint not in TRUSTED_PZSERVER_APIS:
        if hub is not None:
            raise ValueError("JupyterHub credentials require a trusted PzServer API.")
        return None
    if hub is None:
        hub = next(
            (
                os.environ[name]
                for name in ("JUPYTERHUB_PUBLIC_HUB_URL", "JUPYTERHUB_HOST")
                if os.environ.get(name)
            ),
            None,
        )
    if hub is not None:
        hub = normalize_hub_url(hub)
    token = os.environ.get("JUPYTERHUB_API_TOKEN")
    if hub is None or not token:
        return None
    if any(char.isspace() for char in token):
        raise ValueError("Malformed JupyterHub credential.")
    return f"{hub} {token}"


def _token_path(host):
    # Resolve aliases so a token belongs to an API URL, not an arbitrary label.
    endpoint = PzRequests._enviroments.get(host, host).rstrip("/")
    key = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()
    return Path.home() / ".pzserver" / "credentials" / f"{key}.token"


def load_token(host="pz"):
    """Read a saved token without prompting or contacting the API."""
    try:
        token = _token_path(host).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    return token or None


def login(token=None, host="pz"):
    """Validate and save a token, prompting with hidden input when omitted.

    Credentials are stored unencrypted under ``~/.pzserver/credentials``.
    On POSIX, the directory and files are restricted to their owner. The
    home directory must persist for credentials to survive server restarts.
    An existing credential is replaced only after successful validation.
    """
    if token is None:
        # Do not fall back to echoing a secret if hidden input is unavailable.
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            token = getpass.getpass("PzServer API token: ")
    if not isinstance(token, str) or not token.strip():
        raise ValueError("Please provide a valid token.")
    token = token.strip()
    PzRequests(token, host)

    destination = _token_path(host)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination.parent.chmod(0o700)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(token)
        # NamedTemporaryFile creates a private (0600) file on POSIX.
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def logout(host="pz"):
    """Remove the saved token for this API without revoking it on the server.

    Existing PzServer instances keep their in-memory credentials.
    """
    _token_path(host).unlink(missing_ok=True)
