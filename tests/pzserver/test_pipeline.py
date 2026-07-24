"""
Tests for pzserver/pipeline.py
"""

from pzserver.pipeline import Pipeline


class FakeApi:
    def __init__(self):
        self.get_calls = []

    def get_by_name(self, entity, name):
        assert entity == "pipelines"
        assert name == "tsm"
        return {
            "id": 5,
            "display_name": "Training Set Maker",
            "description": "Build training sets",
            "version": "1.2.3",
            "system_config": {"param": {"radius": 1.0}},
            "product_types_accepted": [10, 11],
            "output_product_type": 20,
        }

    def get(self, entity, item_id):
        self.get_calls.append((entity, item_id))
        return {"id": item_id, "name": f"type-{item_id}"}


def test_pipeline_loads_metadata_and_product_types():
    api = FakeApi()

    pipeline = Pipeline("tsm", api)

    assert pipeline.pipeline_id == 5
    assert pipeline.name == "tsm"
    assert pipeline.display_name == "Training Set Maker"
    assert pipeline.description == "Build training sets"
    assert pipeline.version == "1.2.3"
    assert pipeline.system_config == {"param": {"radius": 1.0}}
    assert pipeline.parameters == {"radius": 1.0}
    assert pipeline.acceptable_product_types == (
        {"id": 10, "name": "type-10"},
        {"id": 11, "name": "type-11"},
    )
    assert pipeline.output_product_type == {"id": 20, "name": "type-20"}
    assert api.get_calls == [
        ("product-types", 10),
        ("product-types", 11),
        ("product-types", 20),
    ]
