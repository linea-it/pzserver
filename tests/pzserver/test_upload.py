"""
Tests for pzserver/upload.py
"""

import pytest

from pzserver.upload import PzUpload, RequiredColumnsException, UploadData


class FakeUploadApi:
    def __init__(self, columns=None, fail_columns=False):
        self.basic_info_calls = []
        self.uploaded_files = []
        self.registry_uploads = []
        self.column_updates = []
        self.finished_uploads = []
        self.fail_columns = fail_columns
        self.columns = columns or [
            {"column_name": "RA", "id": 10},
            {"column_name": "Dec", "id": 11},
            {"column_name": "z", "id": 12},
        ]

    def upload_basic_info(self, name, product_type, release, pz_code, description):
        self.basic_info_calls.append((name, product_type, release, pz_code, description))
        return {"id": 99}

    def upload_file(self, product_id, filepath, role, mimetype=None):
        data = {
            "id": len(self.uploaded_files) + 1,
            "product_id": product_id,
            "filepath": filepath,
            "role": role,
            "mimetype": mimetype,
        }
        self.uploaded_files.append(data)
        return data

    def registry_upload(self, product_id):
        self.registry_uploads.append(product_id)

    def get_by_attribute(self, entity, attr, value):
        if self.fail_columns:
            raise RuntimeError("backend unavailable")
        assert (entity, attr, value) == ("product-contents", "product", 99)
        return {"results": self.columns}

    def update_upload_column(self, column_id, data):
        result = {"id": column_id, **data}
        self.column_updates.append((column_id, data))
        return result

    def finish_upload(self, product_id):
        self.finished_uploads.append(product_id)


def test_upload_data_validates_existing_files(tmp_path):
    main_file = tmp_path / "catalog.csv"
    aux_file = tmp_path / "notes.txt"
    main_file.write_text("ra,dec,z\n", encoding="utf-8")
    aux_file.write_text("notes", encoding="utf-8")

    data = UploadData(
        name="catalog",
        product_type="redshift_catalog",
        main_file=str(main_file),
        auxiliary_files=[str(aux_file)],
    )

    assert data.main_file == str(main_file)
    assert data.auxiliary_files == [str(aux_file)]


def test_upload_data_rejects_missing_main_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        UploadData(
            name="catalog",
            product_type="redshift_catalog",
            main_file=str(tmp_path / "missing.csv"),
        )


def test_upload_initialization_saves_metadata_files_and_columns(tmp_path):
    main_file = tmp_path / "catalog.csv"
    aux_file = tmp_path / "notes.txt"
    main_file.write_text("ra,dec,z\n", encoding="utf-8")
    aux_file.write_text("notes", encoding="utf-8")
    api = FakeUploadApi()
    data = UploadData(
        name="catalog",
        product_type="redshift_catalog",
        main_file=str(main_file),
        auxiliary_files=[str(aux_file)],
        release="DR1",
        pz_code="code",
        description="desc",
    )

    upload = PzUpload(data, api)

    assert upload.product_id == 99
    assert api.basic_info_calls == [
        ("catalog", "redshift_catalog", "DR1", "code", "desc")
    ]
    assert [item["role"] for item in api.uploaded_files] == ["main", "auxiliary"]
    assert api.uploaded_files[0]["mimetype"] == "text/csv"
    assert api.registry_uploads == [99]
    assert set(upload.columns) == {"RA", "Dec", "z"}
    assert str(upload) == "catalog"


def test_upload_handles_missing_column_metadata(tmp_path):
    main_file = tmp_path / "catalog.csv"
    main_file.write_text("ra,dec,z\n", encoding="utf-8")
    api = FakeUploadApi(fail_columns=True)
    data = UploadData(
        name="catalog",
        product_type="other",
        main_file=str(main_file),
    )

    upload = PzUpload(data, api)

    assert upload.columns is None


def test_upload_column_association_save_and_reset(tmp_path):
    main_file = tmp_path / "catalog.csv"
    main_file.write_text("ra,dec,z\n", encoding="utf-8")
    api = FakeUploadApi()
    upload = PzUpload(
        UploadData(
            name="catalog",
            product_type="redshift_catalog",
            main_file=str(main_file),
        ),
        api,
    )

    upload.make_columns_association({"RA": "ra", "Dec": "dec", "z": "z"})

    assert upload.check_required_columns() == {
        "success": True,
        "message": "All required columns filled",
    }
    assert api.column_updates[:3] == [
        (10, {"ucd": "pos.eq.ra;meta.main", "alias": "RA"}),
        (11, {"ucd": "pos.eq.dec;meta.main", "alias": "Dec"}),
        (12, {"ucd": "src.redshift", "alias": "z"}),
    ]

    upload.reset_columns_association()

    assert api.column_updates[-3:] == [
        (10, {"ucd": "", "alias": ""}),
        (11, {"ucd": "", "alias": ""}),
        (12, {"ucd": "", "alias": ""}),
    ]


def test_upload_save_rejects_missing_required_columns(tmp_path):
    main_file = tmp_path / "catalog.csv"
    main_file.write_text("ra,dec,z\n", encoding="utf-8")
    api = FakeUploadApi()
    upload = PzUpload(
        UploadData(
            name="catalog",
            product_type="redshift_catalog",
            main_file=str(main_file),
        ),
        api,
    )

    with pytest.raises(RequiredColumnsException, match="Required columns"):
        upload.save()

    assert api.finished_uploads == []


def test_upload_save_finishes_training_set_after_required_column(tmp_path):
    main_file = tmp_path / "catalog.csv"
    main_file.write_text("z\n0.1\n", encoding="utf-8")
    api = FakeUploadApi(columns=[{"column_name": "z", "id": 12}])
    upload = PzUpload(
        UploadData(
            name="training",
            product_type="training_set",
            main_file=str(main_file),
        ),
        api,
    )

    upload.make_columns_association({"z": "z"})
    upload.save()

    assert api.finished_uploads == [99]
