"""
Classes responsible for managing user interaction with products
"""

import mimetypes


class PzProduct:
    """Responsible for managing user interactions with product."""

    def __init__(self, product_id, api):
        """
        PzProduct class constructor
        Args:
            product_id (int): product id
            api (PzRequests): PzRequests instance
        """
        self.api = api
        self.__product_id = product_id

    @property
    def product_id(self):
        """Get product id"""
        return self.__product_id

    def attach_auxiliary_file(self, filepath):
        """Attach auxiliary file
        Args:
            filepath (str): file path
        """

        data = self.api.upload_file(
            self.product_id, filepath, "auxiliary",
            mimetype=self.__check_mimetype(filepath)
        )

        return data.get("id")

    @staticmethod
    def __check_mimetype(filepath):
        return mimetypes.guess_type(filepath)[0]
