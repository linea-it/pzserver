import pytest

from pzserver.process import Process


class FakePipeline:
    def __init__(self, name, api):
        self.pipeline_id = 7
        self.display_name = name
        self.parameters = {
            "combine_type": "concatenate",
            "flags_translation_file": "default-flags.yml",
        }
        self.acceptable_product_types = (
            {"id": 100, "name": "redshift_catalog"},
            {"id": 200, "name": "training_set"},
        )
        self.output_product_type = {"id": 300, "name": "combined_redshift"}


class FakeApi:
    def __init__(self):
        self.started_process = None
        self.started_files = None
        self.stopped = []

    def start_process(self, data, files=None):
        self.started_process = data
        self.started_files = files
        return {"id": 11, "upload": 22}

    def get(self, entity, _id):
        if entity == "products":
            return {
                "id": _id,
                "display_name": "output",
                "internal_name": "22_output",
                "product_type": 100,
            }
        if entity == "processes":
            return {"status": "Pending"}
        if entity == "releases":
            return {"id": _id, "name": "DR1"}
        return {}

    def get_by_attribute(self, entity, attribute, value):
        if (entity, attribute, value) == ("products", "internal_name", "input"):
            return {
                "results": [
                    {
                        "id": 33,
                        "display_name": "Input",
                        "internal_name": "input",
                        "product_type": 100,
                    }
                ]
            }
        return {"results": []}

    def get_by_name(self, entity, name):
        if (entity, name) == ("releases", "DR1"):
            return {"id": 44, "name": "DR1"}
        return None

    def stop_process(self, process_id):
        self.stopped.append(process_id)
        return {"stopped": process_id}


def test_process_level_config_is_sent_outside_param(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    api = FakeApi()
    process = Process("combine_redshift_dedup", "crc hats", api)

    process.set_config(
        {
            "combine_type": "concatenate_and_mark_duplicates",
            "output_format": "hats",
        }
    )
    process.run()

    assert api.started_process["used_config"] == {
        "param": {
            "combine_type": "concatenate_and_mark_duplicates",
            "flags_translation_file": "default-flags.yml",
        },
        "output_format": "hats",
    }


def test_process_manages_inputs_products_status_and_stop(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    api = FakeApi()
    process = Process("combine_redshift_dedup", "crc", api)

    assert process.available_product_types() == ["redshift_catalog", "training_set"]
    assert process.available_product_types_id() == [100, 200]
    assert process.output is None
    assert process.process is None
    assert process.check_status() == "The process has not been started"
    assert process.stop() == "No process is running"

    product = process.get_product(internal_name="input")
    process.append_input(product["id"])
    process.append_input(99)
    assert process.inputs == [33, 99]
    process.empty_input()
    assert process.inputs == []

    result = process.run()

    assert result == {
        "output": {"id": 22, "display_name": "output", "internal_name": "22_output"},
        "id": 11,
        "status": "Pending",
    }
    assert process.output == {
        "id": 22,
        "display_name": "output",
        "internal_name": "22_output",
    }
    assert process.stop() == {"stopped": 11}
    assert api.stopped == [11]
    assert process.run() == {}


def test_process_rejects_missing_or_unexpected_products(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    api = FakeApi()
    process = Process("combine_redshift_dedup", "crc", api)

    with pytest.raises(ValueError, match="No product selected"):
        process.get_product()

    api.get = lambda entity, _id: {"id": _id, "product_type": 999}

    with pytest.raises(ValueError, match="expected type"):
        process.get_product(product_id=1)


def test_training_set_maker_configures_release_input_and_submission(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    from pzserver.process import TSMProcess

    api = FakeApi()
    process = TSMProcess("training set", api)

    process.set_release(name="DR1")
    process.set_redshift(internal_name="input")
    result = process.run()

    assert process.release == {"id": 44, "name": "DR1"}
    assert process.redshift["id"] == 33
    assert process.inputs == [33]
    assert api.started_process == {
        "pipeline": 7,
        "used_config": {
            "param": {
                "combine_type": "concatenate",
                "flags_translation_file": "default-flags.yml",
            }
        },
        "display_name": "training set",
        "release": 44,
        "inputs": [33],
        "id": 11,
    }
    assert result["status"] == "Pending"


def test_training_set_maker_rejects_missing_release(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    from pzserver.process import TSMProcess

    process = TSMProcess("training set", FakeApi())

    with pytest.raises(ValueError, match="No release selected"):
        process.set_release()


def test_combine_redshift_process_tracks_unique_catalogs_and_uploads_flags(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    from pzserver.process import CRCProcess

    api = FakeApi()
    process = CRCProcess("combined", api)
    flags_file = tmp_path / "flags.yml"
    flags_file.write_text("flags: []", encoding="utf-8")

    process.append_catalog(internal_name="input")
    process.append_catalog(internal_name="input")
    process.set_flags_translation(str(flags_file))
    result = process.run()

    assert process.inputs == [33]
    assert process.input_catalogs == [
        {"name": "Input", "internal_name": "input", "id": 33}
    ]
    assert api.started_files["flags_translation_file"].name == str(flags_file)
    assert api.started_process["used_config"]["param"]["flags_translation_file"] == str(
        flags_file
    )
    assert result["id"] == 11
