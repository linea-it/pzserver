from pzserver.process import Process


class FakePipeline:
    def __init__(self, name, api):
        self.pipeline_id = 7
        self.display_name = name
        self.parameters = {"combine_type": "concatenate"}
        self.acceptable_product_types = ()
        self.output_product_type = {}


class FakeApi:
    def __init__(self):
        self.started_process = None

    def start_process(self, data, files=None):
        self.started_process = data
        return {"id": 11, "upload": 22}

    def get(self, entity, _id):
        if entity == "products":
            return {
                "id": _id,
                "display_name": "output",
                "internal_name": "22_output",
            }
        if entity == "processes":
            return {"status": "Pending"}
        return {}


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
        "param": {"combine_type": "concatenate_and_mark_duplicates"},
        "output_format": "hats",
    }
