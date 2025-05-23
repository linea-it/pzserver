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
            product_id (str or int): data product
                unique identifier (product id
                number or internal_name)
            api (PzRequests): PzRequests instance
        """
        self.__api = api

        try:
            if isinstance(product_id, int) or product_id.isdigit():
                metaprod = dict(self.__api.get("products", product_id))
            else:
                plist = self.__api.get_products({"internal_name": product_id})
                metaprod = dict(plist[0])
        except Exception as excp:
            msg = "product not found.\n"
            msg += "Please find the list of products available with "
            msg += "display_products_list() or get_products_list()"
            raise ValueError(msg) from excp

        self.__attributes = metaprod
        self.__product_id = self.__attributes.get("id")
        self.main_file, self.__files = self.__get_files()

    @property
    def product_id(self):
        """Get product id"""
        return self.__product_id

    @property
    def attributes(self):
        """Get product attributes"""
        return self.__attributes

    def __get_files(self):
        """Get files by product id
        Returns:
            tuple: main file and list of files
        """

        files = self.__api.get_product_files(self.product_id)
        main_file = {}
        _files = []

        for file in files:
            if file.get("role_name") != "Main":
                _files.append(file)
            else:
                main_file.update(file)

        return main_file, _files

    def attach_auxiliary_file(self, filepath):
        """Attach auxiliary file
        Args:
            filepath (str): file path
        """
        return self.__attach_file(filepath, "auxiliary")

    def attach_description_file(self, filepath):
        """Attach description file
        Args:
            filepath (str): file path
        """
        return self.__attach_file(filepath, "description")

    def get_auxiliary_files(self):
        """Get auxiliary files
        Returns:
            list: list of auxiliary files
        """

        return self.__get_files_by_type("Auxiliary")

    def get_description_files(self):
        """Get description files
        Returns:
            list: list of description files
        """

        return self.__get_files_by_type("Description")

    def remove_file(self, file_id):
        """Remove file
        Args:
            file_id (int): file id
        """

        if self.__attributes.get("is_owner", False) is False:
            raise ValueError("You are not the owner of this product")

        if file_id == self.main_file.get("id", None):
            raise ValueError("Cannot remove main file")

        for file in self.__files:
            if file.get("id") == file_id and file.get("can_delete", False)\
                  and file.get("role_name") != "Main":
                self.__api.delete_product_file(file_id)
                self.__files.remove(file)
                break

    def update_description(self, description):
        """Update description
        Args:
            description (str): description
        """

        if self.__attributes.get("is_owner", False) is False:
            raise ValueError("You are not the owner of this product")

        self.__api.update_product_description(self.product_id, description)
        self.__attributes["description"] = description

    def __attach_file(self, filepath, file_type):
        """Attach description file
        Args:
            filepath (str): file path
            file_type (str): file type
        """

        if self.__attributes.get("is_owner", False) is False:
            raise ValueError("You are not the owner of this product")

        data = self.__api.upload_file(
            self.product_id, filepath, file_type,
            mimetype=self.__check_mimetype(filepath)
        )

        self.__files.append(data)
        self.__get_files()

    def __get_files_by_type(self, file_type):
        """Get a files by type
        Args:
            file_type (str): file type
        Returns:
            list: list of files
        """

        auxfiles = []

        for file in self.__files:
            if file.get("role_name") == file_type:
                auxfiles.append(file)

        return auxfiles

    @staticmethod
    def __check_mimetype(filepath):
        return mimetypes.guess_type(filepath)[0]
