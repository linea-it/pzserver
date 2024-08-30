"""
Classes responsible for managing user interaction with CSC processes
"""

from pzserver.process import Process

FONTCOLORERR = "\033[38;2;255;0;0m"
FONTCOLOREND = "\033[0m"


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

        dn_specz = {
            "name": specz.get("display_name"),
            "internal_name": specz.get("internal_name"),
            "id": specz.get("id"),
        }

        self.__catalogs.append(dn_specz)
        self.append_input(specz.get("id"))

    def summary(self, extra_info=None):
        """Summary of what will be executed"""

        extra_info = [f"Input catalogs: {self.__catalogs}"]
        super().summary(extra_info=extra_info)
