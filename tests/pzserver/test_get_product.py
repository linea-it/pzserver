"""
Tests for product retrieval behavior.
"""

import importlib.util
import sys
import zipfile
from pathlib import Path
from types import ModuleType
from unittest import mock

import pandas as pd
import pytest
import requests
from astropy.table import Table


def load_core_module():
    root = Path(__file__).parents[2] / "src" / "pzserver"
    package = ModuleType("pzserver")
    package.__path__ = [str(root)]

    sys.modules.setdefault("pzserver", package)
    spec = importlib.util.spec_from_file_location(
        "pzserver.core",
        root / "core.py",
        submodule_search_locations=[str(root)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["pzserver.core"] = module
    spec.loader.exec_module(module)
    return module


def make_server_with_api(core, api):
    server = object.__new__(core.PzServer)
    server.api = api
    return server


def base_metadata(main_file):
    return {
        "id": 42,
        "product_type_internal_name": "redshift_catalog",
        "main_file": main_file,
    }


def test_get_product_rejects_products_larger_than_200_mb():
    core = load_core_module()
    api = mock.Mock()
    server = make_server_with_api(core, api)
    metadata = base_metadata(
        {
            "extension": ".parquet",
            "is_directory": False,
            "name": "main.parquet",
            "size": 200 * 1024 + 1,
        }
    )
    metadata["internal_name"] = "874_test_crc"
    server.get_product_metadata = mock.Mock(return_value=metadata)

    with pytest.raises(ValueError, match="larger than 200 MB") as exc_info:
        server.get_product("874_test_crc")

    message = str(exc_info.value)
    assert "pz_server.download_product" in message
    assert "pandas, Dask, or LSDB" in message
    assert "get_big_products=True" in message
    api.download_main_file.assert_not_called()


def test_get_product_allows_large_products_when_explicitly_requested(tmp_path):
    core = load_core_module()
    table_path = tmp_path / "large.parquet"
    api = mock.Mock()
    api.download_main_file.return_value = {
        "success": True,
        "message": str(table_path),
    }
    server = make_server_with_api(core, api)
    server.get_product_metadata = mock.Mock(
        return_value=base_metadata(
            {
                "extension": ".parquet",
                "is_directory": False,
                "name": "large.parquet",
                "size": 200 * 1024 + 1,
            }
        )
    )

    expected = Table({"id": [1]})
    with mock.patch.object(core.tables_io, "read", return_value=expected):
        result = server.get_product("large", get_big_products=True)

    assert result is expected
    api.download_main_file.assert_called_once()


def test_get_product_allows_product_at_exactly_200_mb(tmp_path):
    core = load_core_module()
    table_path = tmp_path / "limit.parquet"
    api = mock.Mock()
    api.download_main_file.return_value = {
        "success": True,
        "message": str(table_path),
    }
    server = make_server_with_api(core, api)
    server.get_product_metadata = mock.Mock(
        return_value=base_metadata(
            {
                "extension": ".parquet",
                "is_directory": False,
                "name": "limit.parquet",
                "size": 200 * 1024,
            }
        )
    )

    expected = Table({"id": [1]})
    with mock.patch.object(core.tables_io, "read", return_value=expected):
        result = server.get_product("limit")

    assert result is expected
    api.download_main_file.assert_called_once()


class FakeLsdbCatalog:  # pylint: disable=too-few-public-methods
    """Minimal fake LSDB catalog used by get_product tests."""
    def compute(self):
        return pd.DataFrame(
            {
                "object_id": [1, 2],
                "ra": [10.0, 20.0],
                "dec": [-10.0, -20.0],
            }
        )


def create_hats_archive(path, root=""):
    prefix = f"{root.rstrip('/')}" if root else ""
    prefix = f"{prefix}/" if prefix else ""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{prefix}collection.properties", "catalog_name=test\n")
        archive.writestr(f"{prefix}dataset/Norder=0/Dir=0/Npix=0.parquet", b"fake")


def test_get_product_downloads_hats_main_file_and_reads_with_lsdb(tmp_path, monkeypatch):
    core = load_core_module()
    fake_lsdb = ModuleType("lsdb")
    open_catalog = mock.Mock(return_value=FakeLsdbCatalog())
    fake_lsdb.open_catalog = open_catalog
    monkeypatch.setitem(sys.modules, "lsdb", fake_lsdb)

    archive_path = tmp_path / "hats.zip"
    create_hats_archive(archive_path)

    api = mock.Mock()
    api.download_main_file.return_value = {
        "success": True,
        "message": str(archive_path),
    }
    server = make_server_with_api(core, api)
    server.get_product_metadata = mock.Mock(
        return_value=base_metadata(
            {
                "extension": "",
                "is_directory": True,
                "name": "main",
            }
        )
    )

    table = server.get_product("hats_product")

    assert isinstance(table, Table)
    assert table.colnames == ["object_id", "ra", "dec"]
    assert len(table) == 2
    api.download_main_file.assert_called_once()
    api.download_product.assert_not_called()
    assert open_catalog.call_args.kwargs["path"].endswith("/extracted")


def test_get_product_reads_zip_download_even_when_metadata_is_not_directory(
    tmp_path, monkeypatch
):
    core = load_core_module()
    fake_lsdb = ModuleType("lsdb")
    open_catalog = mock.Mock(return_value=FakeLsdbCatalog())
    fake_lsdb.open_catalog = open_catalog
    monkeypatch.setitem(sys.modules, "lsdb", fake_lsdb)

    archive_path = tmp_path / "hats.zip"
    create_hats_archive(archive_path)

    api = mock.Mock()
    api.download_main_file.return_value = {
        "success": True,
        "message": str(archive_path),
    }
    server = make_server_with_api(core, api)
    server.get_product_metadata = mock.Mock(
        return_value=base_metadata(
            {
                "extension": ".parquet",
                "is_directory": False,
                "name": "main",
            }
        )
    )

    table = server.get_product("hats_product")

    assert isinstance(table, Table)
    assert table.colnames == ["object_id", "ra", "dec"]
    api.download_main_file.assert_called_once()
    api.download_product.assert_not_called()
    assert open_catalog.call_args.kwargs["path"].endswith("/extracted")


def test_get_product_raises_when_hats_main_file_download_fails(monkeypatch):
    core = load_core_module()
    fake_lsdb = ModuleType("lsdb")
    fake_lsdb.open_catalog = mock.Mock(return_value=FakeLsdbCatalog())
    monkeypatch.setitem(sys.modules, "lsdb", fake_lsdb)

    api = mock.Mock()
    api.download_main_file.return_value = {
        "success": False,
        "message": "HATS main file download failed",
    }
    server = make_server_with_api(core, api)
    server.get_product_metadata = mock.Mock(
        return_value=base_metadata(
            {
                "extension": "",
                "is_directory": True,
                "name": "main",
            }
        )
    )

    with pytest.raises(requests.exceptions.RequestException, match="HATS"):
        server.get_product("hats_product")

    api.download_main_file.assert_called_once()
    api.download_product.assert_not_called()


def test_get_product_requires_lsdb_for_hats(monkeypatch):
    core = load_core_module()
    monkeypatch.setitem(sys.modules, "lsdb", None)
    api = mock.Mock()
    server = make_server_with_api(core, api)
    server.get_product_metadata = mock.Mock(
        return_value=base_metadata(
            {
                "extension": "",
                "is_directory": True,
                "name": "main",
            }
        )
    )

    with pytest.raises(ImportError, match="lsdb"):
        server.get_product("hats_product")
