"""Keep tests isolated from the user's saved credentials."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for name in (
        "JUPYTERHUB_API_TOKEN", "JUPYTERHUB_HOST", "JUPYTERHUB_PUBLIC_HUB_URL"
    ):
        monkeypatch.delenv(name, raising=False)
