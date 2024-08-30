"""
Classes responsible for managing user interaction with TSM processes
"""

from pzserver.process import Process

FONTCOLORERR = "\033[38;2;255;0;0m"
FONTCOLOREND = "\033[0m"


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

        self.__specz = self.get_product(product_id=specz_id, internal_name=internal_name)
        self.append_input(self.specz.get("id"))

    def summary(self, extra_info=None):
        """Summary of what will be executed"""

        dn_specz = {
            "name": self.specz.get("display_name"),
            "internal_name": self.specz.get("internal_name"),
            "id": self.specz.get("id"),
        }

        extra_info = [f"Specz: {dn_specz}"]
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
    