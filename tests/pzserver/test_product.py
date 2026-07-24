"""
Tests for pzserver/product.py
"""

import pytest

from pzserver.product import PzProduct


class FakeProductApi:
    def __init__(self, is_owner=True):
        self.deleted_files = []
        self.description_updates = []
        self.uploads = []
        self.product = {
            "id": 42,
            "internal_name": "42_product",
            "description": "old",
            "is_owner": is_owner,
        }
        self.files = [
            {"id": 1, "role_name": "Main", "name": "main.parquet"},
            {"id": 2, "role_name": "Auxiliary", "name": "aux.txt", "can_delete": True},
            {
                "id": 3,
                "role_name": "Description",
                "name": "desc.md",
                "can_delete": True,
            },
            {"id": 4, "role_name": "Auxiliary", "name": "locked.txt"},
        ]

    def get(self, entity, item_id):
        assert entity == "products"
        assert str(item_id) == "42"
        return self.product

    def get_products(self, filters):
        assert filters == {"internal_name": "42_product"}
        return [self.product]

    def get_product_files(self, product_id):
        assert product_id == 42
        return [dict(item) for item in self.files]

    def get_main_file_info(self, product_id):
        return {"product": product_id, "size": 123}

    def delete_product_file(self, file_id):
        self.deleted_files.append(file_id)

    def update_product_description(self, product_id, description):
        self.description_updates.append((product_id, description))

    def upload_file(self, product_id, filepath, file_type, mimetype=None):
        data = {
            "id": 100 + len(self.uploads),
            "product": product_id,
            "filepath": filepath,
            "role_name": file_type.title(),
            "mimetype": mimetype,
        }
        self.uploads.append(data)
        return data


def test_product_loads_by_numeric_id_and_groups_files():
    api = FakeProductApi()

    product = PzProduct(42, api)

    assert product.product_id == 42
    assert product.attributes["internal_name"] == "42_product"
    assert product.main_file["id"] == 1
    assert [item["id"] for item in product.get_auxiliary_files()] == [2, 4]
    assert [item["id"] for item in product.get_description_files()] == [3]
    assert product.get_main_file_info() == {"product": 42, "size": 123}


def test_product_loads_by_internal_name():
    product = PzProduct("42_product", FakeProductApi())

    assert product.product_id == 42


def test_product_update_description_requires_ownership():
    api = FakeProductApi(is_owner=False)
    product = PzProduct(42, api)

    with pytest.raises(ValueError, match="not the owner"):
        product.update_description("new")


def test_product_update_description_changes_remote_and_local_state():
    api = FakeProductApi()
    product = PzProduct(42, api)

    product.update_description("new description")

    assert api.description_updates == [(42, "new description")]
    assert product.attributes["description"] == "new description"


def test_product_remove_file_rejects_main_file_and_removes_deletable_aux_file():
    api = FakeProductApi()
    product = PzProduct(42, api)

    with pytest.raises(ValueError, match="Cannot remove main file"):
        product.remove_file(1)

    product.remove_file(2)

    assert api.deleted_files == [2]
    assert [item["id"] for item in product.get_auxiliary_files()] == [4]


def test_product_attach_file_requires_ownership():
    api = FakeProductApi(is_owner=False)
    product = PzProduct(42, api)

    with pytest.raises(ValueError, match="not the owner"):
        product.attach_auxiliary_file("notes.txt")


def test_product_attach_auxiliary_and_description_files():
    api = FakeProductApi()
    product = PzProduct(42, api)

    product.attach_auxiliary_file("notes.txt")
    product.attach_description_file("README.md")

    assert api.uploads[0]["role_name"] == "Auxiliary"
    assert api.uploads[0]["mimetype"] == "text/plain"
    assert api.uploads[1]["role_name"] == "Description"
    assert api.uploads[1]["mimetype"] == "text/markdown"


def test_product_raises_helpful_error_when_product_is_missing():
    class MissingApi(FakeProductApi):
        def get(self, entity, item_id):
            raise KeyError(item_id)

    with pytest.raises(ValueError, match="product not found"):
        PzProduct(42, MissingApi())
