"""Pipeline package"""


class Pipeline:
    """Pipeline data class"""

    def __init__(self, name, api):
        """Initialize pipeline data class

        Args:
            name: pipeline name
            api: PzRequests
        """

        self.__api = api
        self.__data = self.__api.get_by_name("pipelines", name)
        self.__data["name"] = name

        acceptable_product_types = []

        for typeid in self.__data.get("product_types_accepted", []):
            typeobj = self.__api.get("product-types", typeid)
            acceptable_product_types.append(typeobj)

        self.acceptable_product_types = tuple(acceptable_product_types)

        self.output_product_type = self.__api.get(
            "product-types", self.__data.get("output_product_type")
        )

    @property
    def pipeline_id(self):
        """Get pipeline ID

        Returns:
            int: pipeline ID
        """
        return self.__data.get("id")

    @property
    def name(self):
        """Get pipeline name

        Returns:
            str: pipeline name
        """
        return self.__data.get("name")

    @property
    def display_name(self):
        """Get pipeline display name

        Returns:
            str: pipeline display name
        """
        return self.__data.get("display_name", None)

    @property
    def system_config(self):
        """Get pipeline config

        Returns:
            dict: pipeline config
        """
        return self.__data.get("system_config", {})

    @property
    def parameters(self):
        """Get pipeline parameters

        Returns:
            dict: pipeline parameters
        """
        return self.system_config.get("param", {})

    @property
    def version(self):
        """Get pipeline version

        Returns:
            str: pipeline version
        """
        return self.__data.get("version", None)

    @property
    def description(self):
        """Get pipeline description

        Returns:
            str: pipeline description
        """
        return self.__data.get("description", None)
