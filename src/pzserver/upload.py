"""
Classes responsible for managing user interaction
"""

import mimetypes
import pathlib
from typing import Optional

from pydantic import BaseModel, validator


class RequiredColumnsException(Exception):
    """Required columns exception"""

    pass


class UploadData(BaseModel):
    """Upload data"""

    name: str
    product_type: str
    main_file: str
    release: Optional[str] = None
    pz_code: Optional[str] = None
    auxiliary_files: Optional[list] = []
    description: Optional[str] = None

    @property
    def system_columns(self):
        """Returns system columns"""
        return {
            "id": ("ID", "meta.id;meta.main"),
            "ra": ("RA", "pos.eq.ra;meta.main"),
            "dec": ("Dec", "pos.eq.dec;meta.main"),
            "z": ("z", "src.redshift"),
            "z_err": ("z_err", "stat.error;src.redshift"),
            "z_flag": ("z_flag", "stat.rank"),
            "survey": ("survey", "meta.curation"),
        }

    @validator("main_file", pre=True)
    def validate_main_file(cls, value):  # pylint: disable=no-self-argument
        """Validate main_file field"""
        cls.__file_exist(value)
        return value

    @validator("auxiliary_files", pre=True)
    def validate_auxiliary_files(cls, value):  # pylint: disable=no-self-argument
        """Validate auxiliary_files"""
        if value:
            for aux in value:
                cls.__file_exist(aux)
        return value

    @staticmethod
    def __file_exist(filepath):
        """Verify if path exist"""
        _file = pathlib.Path(filepath)
        if not _file.is_file():
            raise FileNotFoundError(f"{_file} not found")


class PzUpload:
    """Responsible for managing user interactions with upload."""

    def __init__(self, upload: UploadData, api):
        """
        PzUpload class constructor

        Args:
            upload (Upload)
            api (PzRequests)
        """

        self.api = api
        self.upload = upload
        self.product_id = self.__save_basic_info()
        self.files_id = []
        self.__save_upload_files()
        self.api.registry_upload(self.product_id)
        self.__columns = self.get_product_columns()
        self.__columns_association = []

    @property
    def columns(self):
        """Get columns"""
        if not self.__columns:
            return None
        return self.__columns.keys()

    @property
    def system_columns(self):
        """Get system columns"""
        return self.upload.system_columns

    def make_columns_association(self, data: dict):
        """Associates upload columns

        Args:
            data (dict): dictionary with associations
        """

        for key, value in data.items():
            id_attr = self.__columns.get(key)
            col = self.upload.system_columns.get(value.lower(), (value, None))
            data_up = {"ucd": col[1], "alias": col[0]}
            _data = self.api.update_upload_column(id_attr, data_up)
            self.__columns_association.append(_data)

    def reset_columns_association(self):
        """Reset upload columns association"""

        for column in self.__columns_association.copy():
            id_attr = column.get("id")
            self.api.update_upload_column(id_attr, {"ucd": "", "alias": ""})
            self.__columns_association.remove(column)

    def check_required_columns(self):
        """Checks required columns

        Args:
            dict: dictionary with success flag and message
        """

        if self.upload.product_type == "redshift_catalog":
            required_columns = ["Dec", "RA", "z"]
        elif self.upload.product_type == "training_set":
            required_columns = ["z"]
        else:
            required_columns = []

        for column in self.__columns_association:
            attr = column.get("alias")
            if attr in required_columns:
                required_columns.remove(attr)

        if required_columns:
            return {
                "success": False,
                "message": f"Required columns NOT filled: {required_columns}",
            }

        return {"success": True, "message": "All required columns filled"}

    def add_auxiliary_file(self, filepath, update=True):
        """Add auxiliary file to upload
        Args:
            filepath (str): file path
        """

        fid = self.__upload_file(filepath, "auxiliary")
        self.files_id.append(fid)

        if update:
            if not self.upload.auxiliary_files:
                self.upload.auxiliary_files = []

            self.upload.auxiliary_files.append(filepath)

    def __save_basic_info(self):
        """Saves the basic upload information in the database.

        Args:
            product_id (int): product id
        """

        data = self.api.upload_basic_info(
            self.upload.name,
            self.upload.product_type,
            self.upload.release,
            self.upload.pz_code,
            self.upload.description,
        )

        return data.get("id")

    def __save_upload_files(self):
        """Saves the upload files in the database.

        Returns:
            file_ids (list): file ids list
        """

        main_id = self.__upload_file(self.upload.main_file, "main")
        self.files_id.append(main_id)

        if self.upload.auxiliary_files:
            for auxfile in self.upload.auxiliary_files:
                self.add_auxiliary_file(auxfile, update=False)

    def get_product_columns(self):
        """Gets product columns in database

        Returns:
            columns (dict): dict with product columns
        """
        try:
            data = self.api.get_by_attribute(
                "product-contents", "product", self.product_id
            )
            columns = self.__dict_columns(data.get("results"))
        except Exception as _:  # pylint: disable=broad-except
            columns = {}

        return columns

    @staticmethod
    def __dict_columns(items):
        """Returns the product columns in dict

        Args:
            items (list): product columns

        Returns:
            dict: product columns
        """

        columns = {}

        for item in items:
            columns[item.get("column_name")] = item.get("id")

        return columns

    def __upload_file(self, filepath, role):
        """Upload file

        Args:
            filepath (str): filepath
            role (str): file role

        Returns:
            product_id (int): product id
        """

        data = self.api.upload_file(
            self.product_id, filepath, role, mimetype=self.__check_mimetype(filepath)
        )

        return data.get("id")

    @staticmethod
    def __check_mimetype(filepath):
        return mimetypes.guess_type(filepath)[0]

    def save(self):
        """Finishs the upload by modifying the status in the database"""

        check_req = self.check_required_columns()

        if not check_req.get("success", False):
            message = check_req.get("message", "")
            raise RequiredColumnsException(message)

        self.api.finish_upload(self.product_id)

    def __str__(self):
        return self.upload.name
