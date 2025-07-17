"""
Classes responsible for managing user interaction
"""

import tempfile
import time

import pandas as pd
import tables_io
from astropy.table import Table
from IPython.display import display

from .catalog import SpeczCatalog, TrainingSet
from .communicate import PzRequests
from .process import CSCProcess, TSMProcess
from .product import PzProduct
from .upload import PzUpload, UploadData

pd.options.display.max_colwidth = None
pd.options.display.max_columns = 500
pd.options.display.max_rows = 6

FONTCOLORERR = "\033[38;2;255;0;0m"
FONTCOLOREND = "\033[0m"


class PzServer:
    """
    Responsible for managing user interactions with the Pz Server app.
    """

    def __init__(self, token=None, host="pz"):
        """
        PzServer class constructor

        Args:
            token (str): user's token generated on the PZ Server website
            host (str): "pz" (production) or
                        "pz-dev" (test environment) or
                        "localhost" (dev environment) or
                        "api url"
        """

        if token is None:
            raise ValueError(
                f"{FONTCOLORERR}Please provide a valid token.{FONTCOLOREND}"
            )

        self.api = PzRequests(token, host)

    # ---- methods to get general info ----#
    def get_product_types(self) -> list:
        """
        Fetches the list of valid product types.

        Connects to the Photo-z Server's administrative
        database and fetches the list of valid product
        types and their respective short description.

        Returns:
            product types list
        """
        return self.api.get_all("product-types", ordering="order")

    def display_product_types(self):
        """
        Displays the list of product types as dataframe

        Displays a pandas.io.formats.style.Styler object
        mapping the product type names to the corresponding
        descriptions (optimized for use in Jupyter Notebook).
        """
        results_dict = self.get_product_types()
        dataframe = pd.DataFrame(
            results_dict, columns=["display_name", "name", "description"]
        )
        dataframe.rename(
            columns={
                "display_name": "Product Type",
                "name": "product_type",
                "description": "Description",
            },
            inplace=True,
        )
        display(dataframe.style.hide(axis="index"))

    def get_users(self) -> list:
        """
        Fetches the list of registered users.

        Connects to the Photo-z Server's administrative
        database and fetches the list of registered
        users (first/last name and GitHub username).

        Returns:
            users list
        """
        return self.api.get_all("users")

    def display_users(self):
        """
        Displays the list of users as dataframe

        Displays a pandas.io.formats.style.Styler object
        mapping the users to corresponding GitHub usernames
        (optimized for use in Jupyter Notebook).
        """
        results_dict = self.get_users()
        dataframe = pd.DataFrame(results_dict, columns=["username", "last_name"])
        dataframe.rename(
            columns={"username": "GitHub Username", "last_name": "Name"}, inplace=True
        )
        display(dataframe.style.hide(axis="index"))

    def get_releases(self) -> list:
        """
        Fetches the list of valid data releases.

        Connects to the Photo-z Server's administrative
        database and fetches the list of valid LSST
        data releases corresponding to the data products
        available. The resulting list is expected to
        increase over the years of survey operations.

        Returns:
            releases list
        """
        return self.api.get_all("releases")

    def display_releases(self):
        """
        Displays the list of data releases as dataframe

        Displays a pandas.io.formats.style.Styler object
        mapping the the data release tags to their full
        names (optimized for use in Jupyter Notebook).
        """
        results_dict = self.api.get_all("releases")
        dataframe = pd.DataFrame(
            results_dict, columns=["name", "display_name", "description"]
        )
        dataframe.rename(
            columns={
                "name": "Name",
                "display_name": "Release",
                "description": "Description",
            },
            inplace=True,
        )
        display(dataframe.style.hide(axis="index"))

    def get_products_list(self, filters=None) -> list:
        """
        Fetches the list of data products available.

        Connects to the Photo-z Server's database and
        fetches the filtered list of data products
        available.

        Args:
            filters (dict): dictionary with a string
                (or a list of strings) patterns to
                filter the results.

        Returns:
            data products list
        """
        return self.api.get_products(filters)

    def display_products_list(self, filters=None):
        """
        Displays the list of data products as dataframe

        Displays a pandas.io.formats.style.Styler object
        with the list of all products available with the
        metadata informed by the owners (optimized for use
        in Jupyter Notebook).

        Args:
            filters (dict): dictionary with strings
                (or a list of strings) patterns to
                filter the results.
        """
        results_dict = self.get_products_list(filters)
        dataframe = pd.DataFrame(
            results_dict,
            columns=[
                "id",
                "internal_name",
                "display_name",
                "product_type_name",
                "release_name",
                "uploaded_by",
                "official_product",
                "pz_code",
                "description",
                "created_at",
            ],
        )

        dataframe.rename(
            columns={
                "display_name": "product_name",
                "release_name": "release",
                "product_type_name": "product_type",
            },
            inplace=True,
        )

        display(dataframe.style.hide(axis="index"))

    # ---- methods to get data or metadata of one particular product ----#
    def get_product_metadata(self, product_id, mainfile_info=True) -> dict:
        """
        Fetches the product metadata.

        Connects to the Photo-z Server's database and
        fetches the metadata informed by the product
        owner for a particular data product.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal_name)
            mainfile_info (bool, optional): additional
                information from the main file.

        Returns:
            dict of product metadata
        """
        try:
            if isinstance(product_id, int) or product_id.isdigit():
                metaprod = dict(self.api.get("products", product_id))
            else:
                plist = self.api.get_products({"internal_name": product_id})
                metaprod = dict(plist[0])
        except Exception as excp:
            msg = f"product not found.\n{FONTCOLORERR}"
            msg += "Please find the list of products available with "
            msg += "display_products_list() or get_products_list()"
            msg += FONTCOLOREND
            raise ValueError(msg) from excp

        if mainfile_info:
            metaprod["main_file"] = self.api.get_main_file_info(metaprod["id"])

        return metaprod

    def display_product_metadata(self, product_id=None, show=True):
        """
        Displays the metadata informed by the product owner.

        Displays a pandas.io.formats.style.Styler object
        with the metadata informed by the product owner
        (optimized for use in Jupyter Notebook).

        Args:
            product (str or int): data product
                unique identifier (product id
                number or internal_name)
        """

        results_dict = self.get_product_metadata(product_id)

        columns = [
            "id",
            "internal_name",
            "display_name",
            "product_type_name",
            "release_name",
            "uploaded_by",
            "official_product",
            "pz_code",
            "description",
            "created_at",
            "main_file",
        ]
        transposed_list = []
        for key, value in results_dict.items():
            if key in columns:
                if key == "release_name":
                    key = "release"
                if key == "product_type_name":
                    key = "product_type"
                if key == "display_name":
                    key = "product_name"
                if key == "main_file":
                    transposed_list.append({"key": "n_rows", "value": value["n_rows"]})
                    value = value["name"]

                transposed_list.append({"key": key, "value": value})
        dataframe = pd.DataFrame(transposed_list)
        if show:
            display(dataframe.style.hide(axis="index"))
            return None

        return dataframe

    def get_product_object(self, product_id):
        """
        Fetches the product object.

        Connects to the Photo-z Server's database and
        fetches the metadata informed by the product
        owner for a particular data product.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal_name)

        Returns:
            PzProduct object
        """
        return PzProduct(product_id, self.api)

    def download_product(self, product_id=None, save_in="."):
        """
        Download the data to local.

        Connects to the Photo-z Server's database and
        download a compressed zip file containing all
        the data and metadata of a given data product.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal_name)
            save_in (str): location where the file will
                be saved

        """
        print("Connecting to PZ Server...")

        prodid = self.get_product_metadata(product_id, mainfile_info=False)["id"]

        results_dict = self.api.download_product(prodid, save_in)
        if results_dict.get("success", False):
            print(f"File saved as: {results_dict['message']}")
            print("Done!")
        else:
            print(f"{FONTCOLORERR}Error: {results_dict['message']}{FONTCOLORERR}")

    def get_product(self, product_id=None):
        """
        Fetches the data product contents to local.

        Connects to the Photo-z Server's database and
        fetches the tabular data stored as registered
        data product.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal name)
           
        Returns:
            astropy.Table

        """
        print("Connecting to PZ Server...")
        metadata = self.get_product_metadata(product_id)
        prod_type = metadata["product_type_internal_name"]

        if prod_type in ("validation_results", "training_results"):
            msg = f"does not support non-tabular data\n{FONTCOLORERR}"
            msg += "The method get_product() only supports simple tabular "
            msg += "data (product types: redshift_catalog, training_set). "
            msg += f"For {prod_type}, please use method download_product()."
            msg += FONTCOLOREND
            raise ValueError(msg)

        if not metadata["main_file"]:
            raise FileNotFoundError(f"Product ID ({product_id}): main file not found")

        file_extension = metadata["main_file"]["extension"]

        with tempfile.TemporaryDirectory() as tmpdirname:
            results_dict = self.api.download_main_file(metadata["id"], tmpdirname)

            if not results_dict.get("success", False):
                print(f"Error: {results_dict['message']}")
                return None

            file_path = results_dict["message"]
            if file_extension == ".csv":
                # TBD: add CSV to tables_io supported formats
                delimiter = metadata["main_file"].get("delimiter", None)
                has_header = metadata["main_file"].get("has_header", False)
                if has_header:
                    dataframe = pd.read_csv(
                        file_path,
                        header=0,
                        delimiter=delimiter,
                    )
                else:
                    dataframe = pd.read_csv(
                        file_path,
                        header=None,
                        names=metadata["main_file"].get("columns"),
                        delimiter=delimiter,
                    )
                return Table.from_pandas(dataframe)
                        
            table = tables_io.read(file_path, tables_io.types.AP_TABLE)

            return table
                
    def upload(
        self,
        name: str,
        product_type: str,
        main_file: str,
        release: str = None,
        pz_code: str = None,
        auxiliary_files: list = None,
        description: str = None,
    ):
        """Make upload

        Args:
            name (str): name
            product_type (str): product type name
            main_file (str): main file path
            release (str, optional): release name. Defaults to None.
            auxiliary_files (list, optional): auxiliary files path list. Defaults to None.
            pz_code (str, optional): pz code. Defaults to None.
            description (str, optional): description. Defaults to None.

        Args:
            upload (PzUpload): Upload object
        """

        data = {
            "name": name,
            "product_type": product_type,
            "release": release,
            "main_file": main_file,
            "auxiliary_files": auxiliary_files,
            "pz_code": pz_code,
            "description": description,
        }

        prod = UploadData(**data)
        return PzUpload(prod, self.api)

    def delete_product(self, product_id):
        """Delete product

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal_name)
        Raises:
            ValueError: if the user is not the owner of the product
        """

        product = self.get_product_metadata(product_id)

        if product.get("is_owner", False) is False:
            raise ValueError("You are not the owner of this product")

        self.api.delete_product(product.get("id"))

    def __transform_df(self, dataframe, metadata):
        """
        Transforms the dataframe into an object corresponding to
        its product type (currently we have two: redshift_catalog or
        training_set) or returns the dataframe.

        Args:
            dataframe (pandas.DataFrame): dataframe
            metadata (dict): product metadata
        """

        metadata_df = self.display_product_metadata(metadata["id"], show=False)

        if metadata["product_type_internal_name"] == "redshift_catalog":
            results = SpeczCatalog(dataframe, metadata, metadata_df)
        elif metadata["product_type_internal_name"] == "training_set":
            results = TrainingSet(dataframe, metadata, metadata_df)
        else:
            results = dataframe

        return results

    def combine_redshift_catalogs(self, name):
        """
        Make combine redshift

        Args:
            name (str): combine redshift name

        Return:
            CSCProcess: CSCProcess object
        """
        return CSCProcess(name, self.api)

    def training_set_maker(self, name):
        """
        Make training set

        Args:
            name (str): training set name

        Return:
            TSMProcess: TSMProcess object
        """
        return TSMProcess(name, self.api)

    def run_and_wait(self, process):
        """
        Wait for processing to finish (30 minute tolerance time)

        Args:

            process (TSMProcess or CombSpeczProcess): process object

        Return:
            dict: process status
        """

        retry = 60
        process.run()

        print("Process submitted successfully, waiting for completion...")

        while process.check_status() in ("Running", "Pending") and retry:
            time.sleep(30)
            retry = retry - 1

        check_status = process.check_status()

        if retry == 0:
            msg = "This process is taking longer than 30 minutes, please "
            msg += "continue monitoring it asynchronously with the "
            msg += "check_status() method"
            print(f"{FONTCOLORERR}{msg}{FONTCOLOREND}")

        elif check_status == "Failed":
            msg = f"Process failed with the following error: {process.output.get('error')}"
            print(f"{FONTCOLORERR}{msg}{FONTCOLOREND}")

        elif check_status == "Successful":
            msg = f"Done! Results registered as ID={process.output.get('id')} "
            msg += f"(internal_name: {process.output.get('internal_name')})"
            print(msg)
