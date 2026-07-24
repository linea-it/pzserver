"""
Tests for the low-level Pz Server communication helpers.
"""

import json
from pathlib import Path

import pytest
import requests

from pzserver import communicate


def make_api():
    api = object.__new__(communicate.PzRequests)
    api._base_api_url = "https://pz.example.org/api/"
    api._token = "token"
    api._filter_options = {}
    return api


class FakeResponse:
    """Small response fake with the pieces used by PzRequests."""

    def __init__(
        self,
        status_code=200,
        headers=None,
        json_data=None,
        text="",
        chunks=None,
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self._json_data = json_data
        self.text = text
        self._chunks = chunks or []
        self.closed = False

    def json(self):
        return self._json_data

    def iter_content(self, chunk_size):  # pylint: disable=unused-argument
        yield from self._chunks

    def close(self):
        self.closed = True


def test_safe_list_get_returns_value_or_default():
    assert communicate.PzRequests.safe_list_get(["a", "b"], 1, "fallback") == "b"
    assert communicate.PzRequests.safe_list_get(["a"], 2, "fallback") == "fallback"


def test_check_response_handles_json_success_empty_success_and_errors():
    api = make_api()

    success = api._check_response(
        FakeResponse(
            headers={"content-type": "application/json"},
            json_data={"count": 1},
        )
    )
    empty = api._check_response(FakeResponse(status_code=204))
    error = api._check_response(FakeResponse(status_code=500, text="server failed"))

    assert success["success"] is True
    assert success["data"] == {"count": 1}
    assert empty["success"] is True
    assert empty["data"] == ""
    assert error["success"] is False
    assert error["message"] == "server failed"


def test_send_request_uses_session_and_reports_connection_errors(monkeypatch):
    api = make_api()
    sent = []

    class FakeSession:
        def send(self, prerequest, **kwargs):
            sent.append((prerequest, kwargs))
            return FakeResponse(
                headers={"content-type": "application/json"},
                json_data={"ok": True},
            )

    monkeypatch.setattr(communicate.requests, "Session", FakeSession)

    req = requests.Request("GET", "https://pz.example.org/api/products/")
    response = api._send_request(
        req.prepare(),
        stream=True,
        timeout=10,
        verify=False,
        cert="cert.pem",
        proxies={"https": "proxy"},
    )

    assert response["success"] is True
    assert response["data"] == {"ok": True}
    assert sent[0][1] == {
        "stream": True,
        "timeout": 10,
        "verify": False,
        "cert": "cert.pem",
        "proxies": {"https": "proxy"},
    }

    class FailingSession:
        def send(self, prerequest, **kwargs):  # pylint: disable=unused-argument
            raise requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(communicate.requests, "Session", FailingSession)

    failed = api._send_request(req.prepare())

    assert failed["success"] is False
    assert failed["message"] == "Connection Error: offline"


def test_request_builders_prepare_expected_methods_headers_and_payloads():
    api = make_api()
    prepared = []

    def capture(request):
        prepared.append(request)
        return {"success": True, "data": {"ok": True}}

    api._send_request = capture

    assert api._get_request("https://pz.example.org/api/products/", {"page": 1})[
        "success"
    ]
    assert api._options_request("https://pz.example.org/api/products/")["success"]
    assert api._post_request("https://pz.example.org/api/products/", {"name": "x"})[
        "success"
    ]
    assert api._patch_request("https://pz.example.org/api/products/1/", {"name": "y"})[
        "success"
    ]
    assert api._delete_request("https://pz.example.org/api/products/1/")["success"]

    get_req, options_req, post_req, patch_req, delete_req = prepared

    assert get_req.method == "GET"
    assert get_req.url == "https://pz.example.org/api/products/?page=1"
    assert get_req.headers["Authorization"] == "Token token"
    assert options_req.method == "OPTIONS"
    assert json.loads(post_req.body) == {"name": "x"}
    assert post_req.headers["Content-Type"] == "application/json"
    assert patch_req.method == "PATCH"
    assert patch_req.body == "name=y"
    assert delete_req.method == "DELETE"


def test_delete_request_normalizes_bad_request_message():
    api = make_api()
    api._send_request = lambda request: {"success": False, "status_code": 400}

    response = api._delete_request("https://pz.example.org/api/products/1/")

    assert response == {
        "success": False,
        "message": "The server failed to perform the operation.",
        "status_code": 400,
    }


def test_filename_and_download_size_helpers():
    filename = communicate.PzRequests._filename_from_content_disposition(
        'attachment; filename="product.zip"'
    )
    fallback_filename = communicate.PzRequests._filename_from_content_disposition(None)

    assert filename == "product.zip"
    assert fallback_filename == "download"
    assert (
        communicate.PzRequests._download_total_size(
            FakeResponse(headers={"Content-Range": "bytes 3-5/6"})
        )
        == 6
    )
    assert (
        communicate.PzRequests._download_total_size(
            FakeResponse(
                status_code=206,
                headers={"Content-Length": "3"},
            ),
            fallback_size=3,
        )
        == 6
    )
    assert (
        communicate.PzRequests._download_total_size(
            FakeResponse(headers={"Content-Length": "4"})
        )
        == 4
    )
    assert communicate.PzRequests._download_total_size(FakeResponse(), 9) == 9


def test_download_request_writes_file_and_returns_destination(tmp_path):
    api = make_api()
    response = FakeResponse(
        headers={
            "Content-Disposition": 'attachment; filename="catalog.csv"',
            "Content-Length": "11",
        },
        chunks=[b"hello", b" ", b"world"],
    )

    api._download_response = lambda url, start_byte=None: {
        "success": True,
        "response_object": response,
    }

    result = api._download_request("https://pz.example.org/download/", tmp_path)

    destination = Path(result["message"])
    assert result["success"] is True
    assert destination.name == "catalog.csv"
    assert destination.read_bytes() == b"hello world"
    assert response.closed is True


def test_download_request_returns_failed_response_without_creating_file(tmp_path):
    api = make_api()
    api._download_response = lambda url, start_byte=None: {
        "success": False,
        "message": "forbidden",
    }

    result = api._download_request("https://pz.example.org/download/", tmp_path)

    assert result == {"success": False, "message": "forbidden"}
    assert list(tmp_path.iterdir()) == []


def test_check_filters_accepts_mapped_filters_and_rejects_unknown_filters():
    api = make_api()
    api._filter_options["products"] = {
        "filter_classes": [{"name": "product_type_name"}],
        "filterset": ["status"],
        "search": "enabled",
    }

    api._check_filters("products", {"product_type": "training", "search": "demo"})

    with pytest.raises(ValueError, match="Valid filter keys"):
        api._check_filters("products", {"unknown": "bad"})


def test_get_helpers_return_data_and_raise_api_errors():
    api = make_api()
    calls = []

    def get_request(url):
        calls.append(url)
        if url.endswith("/api/"):
            return {"products": "https://pz.example.org/api/products/"}
        if url.endswith("products/"):
            return {"success": True, "data": {"results": [{"id": 1}]}}
        if url.endswith("products/1/"):
            return {"success": True, "data": {"id": 1}}
        if "name=duplicate" in url:
            return {"success": True, "data": {"count": 2, "results": [{}, {}]}}
        if "name=missing" in url:
            return {"success": True, "data": {"count": 0, "results": []}}
        if "name=demo" in url:
            return {"success": True, "data": {"count": 1, "results": [{"id": 7}]}}
        return {"success": False, "message": "api failed"}

    api._get_request = get_request

    assert api.get_entities() == ["products"]
    assert api.get_all("products") == [{"id": 1}]
    assert api.get("products", 1) == {"id": 1}
    assert api.get_by_name("products", "demo") == {"id": 7}
    assert api.get_by_name("products", "missing") is None

    with pytest.raises(requests.exceptions.RequestException, match="unique"):
        api.get_by_name("products", "duplicate")

    with pytest.raises(requests.exceptions.RequestException, match="api failed"):
        api.get("bad", 1)

    assert calls[:3] == [
        "https://pz.example.org/api/",
        "https://pz.example.org/api/products/",
        "https://pz.example.org/api/products/1/",
    ]


def test_upload_and_product_helpers_build_expected_api_calls(tmp_path):
    api = make_api()
    posted = []
    uploaded = []
    patched = []
    got = []

    def get_by_name(entity, name):
        return {"product-types": {"id": 3}, "releases": {"id": 9}}[entity]

    def post_request(url, payload, files=None):
        posted.append((url, payload.copy(), files))
        return {"success": True, "data": {"id": 42, **payload}}

    def upload_request(url, payload, upload_files=None):
        uploaded.append((url, payload.copy(), upload_files.copy()))
        return {"success": True, "data": {"id": 5, **payload}}

    def patch_request(url, data):
        patched.append((url, data.copy()))
        return {"success": True, "data": data}

    def get_request(url):
        got.append(url)
        return {"success": True, "data": {"registry": True}}

    api.get_by_name = get_by_name
    api._post_request = post_request
    api._upload_request = upload_request
    api._patch_request = patch_request
    api._get_request = get_request

    file_path = tmp_path / "main.hdf5"
    file_path.write_text("data", encoding="utf-8")

    basic_info = api.upload_basic_info(
        "demo",
        "training",
        release="DR1",
        pz_code="pz",
        description="description",
    )
    uploaded_file = api.upload_file(42, str(file_path), "main", mimetype="text/csv")
    registry = api.registry_upload(42)
    column = api.update_upload_column(11, {"alias": "z"})
    finished = api.finish_upload(42)
    description = api.update_product_description(42, "new")

    assert basic_info["product_type"] == 3
    assert basic_info["release"] == 9
    assert posted[0][0] == "https://pz.example.org/api/products/"
    assert uploaded_file["role"] == 0
    assert uploaded == [
        (
            "https://pz.example.org/api/product-files/",
            {"product": 42, "role": 0, "type": "text/csv"},
            {"file": str(file_path)},
        )
    ]
    assert registry == {"registry": True}
    assert column == {"alias": "z"}
    assert finished == {"status": 1}
    assert description == {"description": "new"}
    assert got == ["https://pz.example.org/api/products/42/registry/"]
    assert patched == [
        ("https://pz.example.org/api/product-contents/11/", {"alias": "z"}),
        ("https://pz.example.org/api/products/42/", {"status": 1}),
        ("https://pz.example.org/api/products/42/", {"description": "new"}),
    ]


def test_get_products_maps_filters_and_returns_results():
    api = make_api()
    api._filter_options["products"] = {
        "filter_classes": [{"name": "product_type_name"}, {"name": "release_name"}],
        "filterset": ["status"],
    }
    calls = []

    def get_request(url):
        calls.append(url)
        return {"success": True, "data": {"results": [{"id": 1}]}}

    api._get_request = get_request

    result = api.get_products(
        {"product_type": ["training", "validation"], "release": "DR1"}
    )

    assert result == [{"id": 1}]
    assert calls == [
        "https://pz.example.org/api//products/?"
        "status=1&product_type_name=training,validation&release_name=DR1"
    ]
