"""
Tests for product download orchestration.
"""

import importlib.util
from pathlib import Path

import pytest
import requests


def load_communicate_module():
    module_path = Path(__file__).parents[2] / "src" / "pzserver" / "communicate.py"
    spec = importlib.util.spec_from_file_location("pzserver_communicate", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_api():
    communicate = load_communicate_module()
    api = object.__new__(communicate.PzRequests)
    api._base_api_url = "https://pz.example.org/api/"
    api._token = "token"
    return api, communicate


def test_download_product_uses_prepared_download_url(monkeypatch):
    api, _ = make_api()
    calls = []

    monkeypatch.setattr(
        api,
        "_prepare_product_download",
        lambda product_id: {
            "status": "ready",
            "download_url": "/api/products/42/download/file/?token=signed",
        },
    )
    monkeypatch.setattr(
        api,
        "_download_request",
        lambda url, save_in: calls.append((url, save_in))
        or {"success": True, "message": f"{save_in}/product.zip"},
    )

    result = api.download_product(42, "/tmp")

    assert result["success"] is True
    assert calls == [
        ("https://pz.example.org/api/products/42/download/file/?token=signed", "/tmp")
    ]


def test_download_product_polls_until_ready(monkeypatch):
    api, communicate = make_api()
    statuses = [
        {"status": "running"},
        {
            "status": "ready",
            "download_url": "/api/products/42/download/file/?token=signed",
        },
    ]

    monkeypatch.setattr(
        api,
        "_prepare_product_download",
        lambda product_id: {"status": "pending"},
    )
    monkeypatch.setattr(
        api,
        "_get_product_download_status",
        lambda product_id: statuses.pop(0),
    )
    monkeypatch.setattr(
        api,
        "_download_request",
        lambda url, save_in: {"success": True},
    )
    monkeypatch.setattr(communicate.time, "sleep", lambda seconds: None)

    result = api.download_product(42, "/tmp", timeout=10, poll_interval=0)

    assert result["success"] is True
    assert not statuses


def test_download_product_raises_when_archive_failed(monkeypatch):
    api, _ = make_api()

    monkeypatch.setattr(
        api,
        "_prepare_product_download",
        lambda product_id: {"status": "failed", "error_message": "zip failed"},
    )

    with pytest.raises(requests.exceptions.RequestException, match="zip failed"):
        api.download_product(42)
