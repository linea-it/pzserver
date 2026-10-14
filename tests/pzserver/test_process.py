import pytest

from pzserver.process import Process


class FakePipeline:
    def __init__(self, name, api):
        self.pipeline_id = 7
        self.display_name = name
        if name == "training_set_maker":
            self.parameters = {
                "flux_type": "auto",
                "dereddening": "none",
                "convert_flux_to_mag": False,
                "hats_config": {},
            }
        else:
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
        self.release = {
            "id": 44,
            "name": "DR1",
            "can_convert_flux_to_mag": True,
            "fluxes": [
                {"name": "cModel", "display_name": "cModel", "selected": True}
            ],
            "dereddening": [
                {"name": "none", "display_name": "None", "selected": True},
                {"name": "sfd", "display_name": "SFD", "selected": False},
            ],
        }

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
            return {**self.release, "id": _id}
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
            return self.release
        return None

    def get_release_hats_config(self, release_id):
        assert release_id == 44
        return {
            "release": "DR1",
            "config": {
                "input": {
                    "user_selected_cols": ["u_<FLUX>Flux", "u_<FLUX>FluxErr"]
                },
                "photometry": {
                    "measurements": [
                        {
                            "name": "<FLUX>",
                            "input": {
                                "type": "flux",
                                "value_pattern": "BAND_<FLUX>Flux",
                                "error_pattern": "BAND_<FLUX>FluxErr",
                            },
                            "output": {
                                "type": "<MAG_OR_FLUX>_dered",
                                "value_pattern": (
                                    "BAND_<FLUX><MAG_OR_FLUX>_<DEREDDENING>"
                                ),
                                "error_pattern": (
                                    "BAND_<FLUX><MAG_OR_FLUX>Err_<DEREDDENING>"
                                ),
                            },
                        }
                    ]
                },
                "dust": {"use_dustmap": None},
            },
        }

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
    process.set_config(
        {
            "flux_type": "cmodel",
            "dereddening": "sfd",
            "convert_flux_to_mag": True,
        }
    )
    process.set_redshift(internal_name="input")
    result = process.run()

    assert process.release == api.release
    assert process.redshift["id"] == 33
    assert process.inputs == [33]
    assert api.started_process["pipeline"] == 7
    assert api.started_process["display_name"] == "training set"
    assert api.started_process["release"] == 44
    assert api.started_process["inputs"] == [33]

    param = api.started_process["used_config"]["param"]
    assert param["flux_type"] == "cModel"
    assert param["dereddening"] == "sfd"
    assert param["convert_flux_to_mag"] is True
    assert param["hats_config"]["dust"]["use_dustmap"] == "sfd"
    output = param["hats_config"]["photometry"]["measurements"][0]["output"]
    assert output == {
        "type": "mag_dered",
        "value_pattern": "BAND_cModelMag_sfd",
        "error_pattern": "BAND_cModelMagErr_sfd",
    }
    assert result["status"] == "Pending"


def test_training_set_maker_defaults_to_flux_and_uses_release_defaults(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    from pzserver.process import TSMProcess

    process = TSMProcess("training set", FakeApi())
    process.set_release(name="DR1")

    used_config = process.used_config
    param = used_config["param"]
    assert param["flux_type"] == "cModel"
    assert param["dereddening"] == "none"
    assert param["convert_flux_to_mag"] is False
    assert param["hats_config"]["dust"]["use_dustmap"] is None
    output = param["hats_config"]["photometry"]["measurements"][0]["output"]
    assert output == {
        "type": "flux",
        "value_pattern": "BAND_cModelFlux",
        "error_pattern": "BAND_cModelFluxErr",
    }


def test_training_set_maker_uses_advanced_hats_config_unchanged(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    from pzserver.process import TSMProcess

    process = TSMProcess("training set", FakeApi())
    process.set_release(name="DR1")
    advanced_config = {"photometry": {"advanced": True}}
    process.set_config({"hats_config": advanced_config})

    assert process.used_config["param"]["hats_config"] == advanced_config


def test_training_set_maker_rejects_disallowed_magnitude_conversion(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    from pzserver.process import TSMProcess

    api = FakeApi()
    api.release["can_convert_flux_to_mag"] = False
    process = TSMProcess("training set", api)
    process.set_release(name="DR1")
    process.set_config({"convert_flux_to_mag": True})

    with pytest.raises(ValueError, match="does not allow"):
        process.run()


def test_training_set_maker_rejects_missing_release(monkeypatch):
    monkeypatch.setattr("pzserver.process.Pipeline", FakePipeline)
    from pzserver.process import TSMProcess

    process = TSMProcess("training set", FakeApi())

    with pytest.raises(ValueError, match="No release selected"):
        process.set_release()

    with pytest.raises(ValueError, match="No release selected"):
        process.run()


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
