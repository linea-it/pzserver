"""
Tests for the user-facing PzServer facade.
"""

from unittest import mock

import pandas as pd
import pytest

from pzserver import core


def make_server(api):
    server = object.__new__(core.PzServer)
    server.api = api
    return server


class FakeApi:
    def __init__(self):
        self.deleted = []
        self.downloads = []

    def get_all(self, entity, ordering=None):
        return [{"entity": entity, "ordering": ordering}]

    def get_products(self, filters=None):
        if filters == {"internal_name": "named_product"}:
            return [self.product_metadata(8)]
        return [{"filters": filters}]

    def get(self, entity, item_id):
        if entity == "products" and str(item_id) == "404":
            raise RuntimeError("missing")
        return self.product_metadata(int(item_id))

    def get_main_file_info(self, product_id):
        return {
            "name": f"main-{product_id}.csv",
            "n_rows": 2,
            "columns": ["z", "ra"],
            "size": 1_000_000,
        }

    def download_product(self, product_id, save_in):
        self.downloads.append((product_id, save_in))
        return {"success": True, "message": f"{save_in}/product.zip"}

    def delete_product(self, product_id):
        self.deleted.append(product_id)

    @staticmethod
    def product_metadata(product_id, is_owner=True):
        return {
            "id": product_id,
            "internal_name": f"product_{product_id}",
            "display_name": "Product",
            "product_type_name": "Redshift catalog",
            "product_type_internal_name": "redshift_catalog",
            "release_name": "DR1",
            "uploaded_by": "user",
            "official_product": False,
            "pz_code": "code",
            "description": "description",
            "created_at": "today",
            "is_owner": is_owner,
        }


def test_server_requires_token():
    with pytest.raises(ValueError, match="Please provide a valid token"):
        core.PzServer()


def test_simple_list_methods_delegate_to_api():
    server = make_server(FakeApi())

    assert server.get_product_types() == [
        {"entity": "product-types", "ordering": "order"}
    ]
    assert server.get_users() == [{"entity": "users", "ordering": None}]
    assert server.get_releases() == [{"entity": "releases", "ordering": None}]
    assert server.get_products_list({"release": "DR1"}) == [
        {"filters": {"release": "DR1"}}
    ]


def test_get_product_metadata_by_id_and_internal_name():
    server = make_server(FakeApi())

    by_id = server.get_product_metadata(7)
    by_string_id = server.get_product_metadata("7", mainfile_info=False)
    by_name = server.get_product_metadata("named_product")

    assert by_id["id"] == 7
    assert by_id["main_file"]["name"] == "main-7.csv"
    assert "main_file" not in by_string_id
    assert by_name["id"] == 8


def test_get_product_metadata_raises_helpful_error_when_missing():
    server = make_server(FakeApi())

    with pytest.raises(ValueError, match="product not found"):
        server.get_product_metadata("404")


def test_display_product_metadata_can_return_dataframe():
    server = make_server(FakeApi())

    dataframe = server.display_product_metadata(7, show=False)

    assert list(dataframe.columns) == ["key", "value"]
    assert {"key": "product_name", "value": "Product"} in dataframe.to_dict("records")
    assert {"key": "n_rows", "value": 2} in dataframe.to_dict("records")
    assert {"key": "n_columns", "value": 2} in dataframe.to_dict("records")


def test_download_product_resolves_metadata_id_and_reports_success(capsys):
    api = FakeApi()
    server = make_server(api)

    server.download_product("named_product", save_in="/tmp/downloads")

    output = capsys.readouterr().out
    assert api.downloads == [(8, "/tmp/downloads")]
    assert "File saved as: /tmp/downloads/product.zip" in output
    assert "Done!" in output


def test_delete_product_requires_ownership_and_calls_api():
    api = FakeApi()
    server = make_server(api)

    server.delete_product(7)

    assert api.deleted == [7]

    server.get_product_metadata = mock.Mock(
        return_value=FakeApi.product_metadata(9, is_owner=False)
    )

    with pytest.raises(ValueError, match="not the owner"):
        server.delete_product(9)


def test_upload_builds_upload_data_and_upload_object(tmp_path, monkeypatch):
    api = FakeApi()
    server = make_server(api)
    main_file = tmp_path / "main.csv"
    aux_file = tmp_path / "aux.txt"
    main_file.write_text("z\n1\n", encoding="utf-8")
    aux_file.write_text("notes", encoding="utf-8")
    captured = {}

    class FakeUploadData:
        def __init__(self, **kwargs):
            captured["data"] = kwargs

    class FakeUpload:
        def __init__(self, data, upload_api):
            self.data = data
            self.api = upload_api

    monkeypatch.setattr(core, "UploadData", FakeUploadData)
    monkeypatch.setattr(core, "PzUpload", FakeUpload)

    upload = server.upload(
        "demo",
        "training_set",
        str(main_file),
        release="DR1",
        auxiliary_files=[str(aux_file)],
        description="desc",
    )

    assert captured["data"] == {
        "name": "demo",
        "product_type": "training_set",
        "release": "DR1",
        "main_file": str(main_file),
        "auxiliary_files": [str(aux_file)],
        "pz_code": None,
        "description": "desc",
    }
    assert upload.api is api


def test_transform_df_returns_specialized_catalogs_or_dataframe(monkeypatch):
    server = make_server(FakeApi())
    dataframe = pd.DataFrame({"z": [0.1]})
    metadata = {
        "id": 7,
        "product_type_internal_name": "redshift_catalog",
        "main_file": {"columns_association": []},
    }
    server.display_product_metadata = mock.Mock(return_value=pd.DataFrame())

    specz = server.transform_df(dataframe, metadata)
    training = server.transform_df(
        dataframe,
        {
            "id": 7,
            "product_type_internal_name": "training_set",
            "main_file": {"columns_association": []},
        },
    )
    unchanged = server.transform_df(
        dataframe,
        {"id": 7, "product_type_internal_name": "validation_results"},
    )

    assert isinstance(specz, core.SpeczCatalog)
    assert isinstance(training, core.TrainingSet)
    assert unchanged is dataframe


def test_process_factory_methods_and_run_and_wait(monkeypatch, capsys):
    server = make_server(FakeApi())

    monkeypatch.setattr(core, "CRCProcess", lambda name, api: ("crc", name, api))
    monkeypatch.setattr(core, "TSMProcess", lambda name, api: ("tsm", name, api))

    assert server.combine_redshift_catalogs("combined") == (
        "crc",
        "combined",
        server.api,
    )
    assert server.training_set_maker("training") == ("tsm", "training", server.api)

    class FakeProcess:
        def __init__(self):
            self.output = {"id": 1, "internal_name": "done"}
            self.statuses = ["Running", "Successful", "Successful"]

        def run(self):
            return None

        def check_status(self):
            return self.statuses.pop(0)

    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)

    server.run_and_wait(FakeProcess())

    assert "Done! Results registered as ID=1" in capsys.readouterr().out
