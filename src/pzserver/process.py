"""
Classes responsible for managing user interaction with processes
"""

from .pipeline import Pipeline

FONTCOLORERR = "\033[38;2;255;0;0m"
FONTCOLOREND = "\033[0m"


class Process:
    """ Responsible for managing user interactions with process """

    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case.

    def __init__(self, pipeline, name, api):
        """Process class constructor

        Args:
            pipeline (str): Pipeline name
            name (str): Product name
            api (PzRequests): PzRequests
        """

        self.__api = api
        self.name = name
        self.comment = None
        self.pipeline = Pipeline(pipeline, self.__api)
        self.__config = self.pipeline.parameters
        self.__inputs = []
        self.__process = None
        self.__upload = None

    def __available_product_types_by_attribute(self, attr):
        """List the product types available by attribute

        Returns:
            list: product types available
        """
        available_inputs = []

        for producttype in self.pipeline.acceptable_product_types:
            available_inputs.append(producttype.get(attr))

        return available_inputs

    def available_product_types(self):
        """List the product types available

        Returns:
            list: product types available
        """
        return self.__available_product_types_by_attribute("name")

    def available_product_types_id(self):
        """List the product types id available

        Returns:
            list: product types id available
        """
        return self.__available_product_types_by_attribute("id")

    @property
    def output(self):
        """Process output info

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
        """Process info

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
    def inputs(self):
        """Gets inputs

        Returns:
            list: inputs
        """
        return self.__inputs

    def append_input(self, input_id):
        """Append input

        Args:
            input_id (int): input id
        """
        self.__inputs.append(input_id)

    def empty_input(self):
        """ Empty inputs list
        """
        self.__inputs = []

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

    def get_product(self, product_id=None, internal_name=None):
        """_summary_

        Args:
            product_id (int, optional): product ID. Defaults to None.
            internal_name (str, optional): internal name. Defaults to None.

        Raises:
            ValueError: when neither specz_id nor internal_name is informed, the raise is triggered
        """

        if product_id:
            specz = self.__api.get("products", product_id)
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

        return specz

    def summary(self, extra_info=None):
        """Summary of what will be executed"""

        print('-'*30)
        print(f"{self.pipeline.display_name}: {self.name}")
        print(f"Configuration: {self.config}")

        if isinstance(extra_info, list):
            for line in extra_info:
                print(line)

        if self.output:
            print(f"Output: {self.output}")

        print(f"Status: {self.check_status()}")
        print('-'*30)

    def run(self):
        """Starts processing

        Returns:
            dict: process info
        """

        if self.__process:
            print(f"Process has already been initialized: {self.process}")
            return {}

        data_process = {
            "display_name": self.name,
            "used_config": {"param": self.config},
            "pipeline": self.pipeline.pipeline_id,
            "inputs": self.inputs,
        }
        return self.submit(data_process)


    def submit(self, data):
        """Submit process

        Args:
            data (dict): process data

        Returns:
            dict: process info
        """


        process = self.__api.start_process(data)
        data["id"] = process.get("id")
        self.__process = data
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


class TSMProcess(Process):
    """Responsible for managing user interactions with TSM process."""

    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case.

    def __init__(self, name, api):
        """TSM process class constructor

        Args:
            name (str): TSM name
            api (PzRequests): PzRequests
        """

        super().__init__("training_set_maker", name, api)
        self.__api = api
        self.__release = None
        self.__specz = None

    @property
    def release(self):
        """Gets release info

        Returns:
            dict: release info
        """
        return self.__release

    def set_release(self, name=None, release_id=None):
        """Set release

        Args:
            name (str, optional): release name. Defaults to None.
            release_id (int, optional): release ID. Defaults to None.

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


        self.__specz = self.get_product(product_id=specz_id, internal_name=internal_name)
        self.empty_input()
        self.append_input(self.specz.get("id"))

    def summary(self, extra_info=None):
        """Summary of what will be executed"""

        if not extra_info:
            extra_info = []

        if self.specz:
            dn_specz = {
                "name": self.specz.get("display_name"),
                "internal_name": self.specz.get("internal_name"),
                "id": self.specz.get("id"),
            }

            extra_info.append(f"Specz: {dn_specz}")

        if self.release:
            extra_info.append(f"Release: {self.release}")

        super().summary(extra_info=extra_info)


    def run(self):
        """Starts TSM processing

        Returns:
            dict: process info
        """

        if self.process:
            print(f"Process has already been initialized: {self.process}")
            return {}

        data_process = {
            "pipeline": self.pipeline.pipeline_id,
            "used_config": {"param": self.config},
            "display_name": self.name,
            "release": self.release.get("id"),
            "inputs": self.inputs,
        }
        return self.submit(data_process)


class CSCProcess(Process):
    """Responsible for managing user interactions with CSC process."""

    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case.

    def __init__(self, name, api):
        """CSC process class constructor

        Args:
            name (str): CSC name
            api (PzRequests): PzRequests
        """

        super().__init__("combine_specz", name, api)
        # self.__api = api
        self.__catalogs = []

    @property
    def input_catalogs(self):
        """Gets input catalogs

        Returns:
            list: catalog list
        """
        return self.__catalogs

    def append_catalog(self, specz_id=None, internal_name=None):
        """Append specz

        Args:
            specz_id (int, optional): product ID. Defaults to None.
            internal_name (str, optional): internal name. Defaults to None.

        Raises:
            ValueError: when neither specz_id nor internal_name is informed, the raise is triggered
        """

        specz = self.get_product(product_id=specz_id, internal_name=internal_name)
        specz_id = specz.get("id")

        if not specz_id in self.inputs:
            dn_specz = {
                "name": specz.get("display_name"),
                "internal_name": specz.get("internal_name"),
                "id": specz_id,
            }

            self.__catalogs.append(dn_specz)
            self.append_input(specz_id)

    def summary(self, extra_info=None):
        """Summary of what will be executed"""

        if not extra_info:
            extra_info = []

        if self.input_catalogs:
            extra_info.append(f"Input catalogs: {self.input_catalogs}")

        super().summary(extra_info=extra_info)
