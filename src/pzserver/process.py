"""
Classes responsible for managing user interaction with processes
"""

from .pipeline import Pipeline

FONTCOLORERR = "\033[38;2;255;0;0m"
FONTCOLOREND = "\033[0m"


class TSMProcess:
    """Responsible for managing user interactions with TSM process."""

    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case.

    def __init__(self, name, api):
        """TSM process class constructor

        Args:
            name (str): TSM name
            api (PzRequests): PzRequests
        """

        self.__api = api
        self.name = name
        self.comment = None
        self.pipeline = Pipeline("training_set_maker", self.__api)
        self.__config = self.pipeline.parameters
        self.__release = None
        self.__specz = None
        self.__process = None
        self.__upload = None

    def __available_product_types_by_attribute(self, attr):
        """List the product types available for TSM by attribute

        Returns:
            list: product types available
        """
        available_inputs = []

        for producttype in self.pipeline.acceptable_product_types:
            available_inputs.append(producttype.get(attr))

        return available_inputs

    def available_product_types(self):
        """List the product types available for TSM

        Returns:
            list: product types available
        """
        return self.__available_product_types_by_attribute("name")

    def available_product_types_id(self):
        """List the product types id available for TSM

        Returns:
            list: product types id available
        """
        return self.__available_product_types_by_attribute("id")

    @property
    def output(self):
        """TSM output info

        Returns:
            dict: output info
        """
        if not self.__upload:
            return None

        return {
            "id": self.__upload.get("id"),
            "display_name": self.__upload.get("display_name"),
            "internal_name": self.__upload.get("internal_name"),
        }

    @property
    def process(self):
        """TSM process info

        Returns:
            dict: process info
        """
        if not self.__process:
            return None

        return {
            "output": self.output,
            "id": self.__process.get("id"),
            "status": self.check_status(),
        }

    @property
    def release(self):
        """Gets release info

        Returns:
            dict: release info
        """
        return self.__release

    def set_release(self, release_id=None, name=None):
        """Set release

        Args:
            release_id (int, optional): release ID. Defaults to None.
            name (str, optional): release name. Defaults to None.

        Raises:
            ValueError: when neither release_id nor name is informed, the raise is triggered
        """
        if release_id:
            release = self.__api.get("releases", release_id)
        elif name:
            release = self.__api.get_by_name("releases", name)
        else:
            raise ValueError(f"{FONTCOLORERR}No release selected{FONTCOLOREND}")
        self.__release = release

    @property
    def specz(self):
        """Gets specz info

        Returns:
            dict: specz info
        """
        return self.__specz

    def set_specz(self, specz_id=None, internal_name=None):
        """Set specz

        Args:
            specz_id (int, optional): product ID. Defaults to None.
            internal_name (str, optional): internal name. Defaults to None.

        Raises:
            ValueError: when neither specz_id nor internal_name is informed, the raise is triggered
        """
        if specz_id:
            specz = self.__api.get("products", specz_id)
        elif internal_name:
            specz = self.__api.get_by_attribute(
                "products", "internal_name", internal_name
            )
            specz = specz.get("results")[0]
        else:
            raise ValueError(f"{FONTCOLORERR}No specz selected{FONTCOLOREND}")

        specz_pt = specz.get("product_type")

        if not specz_pt in self.available_product_types_id():
            raise ValueError(
                f"{FONTCOLORERR}Input is not of the expected type.{FONTCOLOREND}"
            )

        self.__specz = specz

    @property
    def config(self):
        """Gets config

        Returns:
            dict: config
        """
        return self.__config

    def set_config(self, config):
        """Set config

        Args:
            config (dict): config
        """
        self.__config.update(config)

    @property
    def summary(self):
        """Summary of what will be executed"""

        dn_specz = {
            "name": self.specz.get("display_name"),
            "internal_name": self.specz.get("internal_name"),
            "id": self.specz.get("id"),
        }

        print('-'*30)
        print(f"Training Set Maker: {self.name}")
        print(f"Release: {self.release.get('display_name')}")
        print(f"Specz: {dn_specz}")
        print(f"Configuration: {self.config}")
        if self.output:
            print(f"Output: {self.output}")
        print(f"Status: {self.check_status()}")
        print('-'*30)

    def run(self):
        """Starts TSM processing

        Raises:
            ValueError: Fired when no release is set
            ValueError: Fired when no specz is set

        Returns:
            dict: process info
        """
        if self.__process:
            print(f"Process has already been initialized: {self.process}")
            return {}

        if not self.release:
            raise ValueError(f"{FONTCOLORERR}No release selected{FONTCOLOREND}")

        if not self.specz:
            raise ValueError(f"{FONTCOLORERR}No specz selected{FONTCOLOREND}")

        data_process = {
            "release": self.release.get("id"),
            "display_name": self.name,
            "used_config": {"param": self.config},
            "pipeline": self.pipeline.pipeline_id,
            "inputs": [self.specz.get("id")],
        }

        process = self.__api.start_process(data_process)
        data_process["id"] = process.get("id")
        self.__process = data_process
        self.__upload = self.__api.get("products", process.get("upload"))

        return self.process

    def check_status(self):
        """Checks process status

        Returns:
            dict: process status
        """
        if not self.__process:
            return "The process has not been started"

        process = self.__api.get("processes", self.__process.get("id"))
        return f"{process.get('status')}"

    def stop(self):
        """Stop process

        Returns:
            dict: process info
        """
        if not self.__process:
            return "No process is running"

        return self.__api.stop_process(self.__process.get("id"))
