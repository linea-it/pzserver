""" 
Classes responsible for managing user interaction 
"""

import tempfile

import pandas as pd
import tables_io
from astropy.table import Table
from IPython.display import display

from .catalog import SpeczCatalog, TrainingSet
from .communicate import PzRequests

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
            token: (str): user's token generated on the PZ Server website
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
        self._token = token

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
        return self.api.get_all("product-types")

    def display_product_types(self):
        """
        Displays the list of product types as dataframe

        Displays a pandas.io.formats.style.Styler object
        mapping the product type names to the corresponding
        descriptions (optimized for use in Jupyter Notebook).
        """
        results_dict = self.get_product_types()
        dataframe = pd.DataFrame(results_dict, columns=["display_name", "description"])
        dataframe.rename(
            columns={"display_name": "Product type", "description": "Description"},
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
            columns={"username": "GitHub username", "last_name": "name"}, inplace=True
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
        dataframe = pd.DataFrame(results_dict, columns=["display_name", "description"])
        dataframe.rename(
            columns={"display_name": "Release", "description": "Description"},
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
    def get_product_metadata(self, product_id=None, mainfile_info=True) -> dict:
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
        product_id = str(product_id)
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
                    value = value["name"]
                transposed_list.append({"key": key, "value": value})
        dataframe = pd.DataFrame(transposed_list)
        if show:
            display(dataframe.style.hide(axis="index"))
            return None

        return dataframe

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

    def get_product(self, product_id=None, fmt=None):
        """
        Fetches the data product contents to local.

        Connects to the Photo-z Server's database and
        fetches the tabular data stored as registered
        data product.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal name)
            fmt (str): output table format
                'pandas' -> pandas.DataFrame
                'astropy' -> astropy.Table
                None (default) -> object class from catalog.py

        Returns:
            SpeczCatalog or TrainingSet (pandas.DataFrame extensions)
            object, or pure pandas.DataFrame, or astropy.Table

        """
        print("Connecting to PZ Server...")
        metadata = self.get_product_metadata(product_id)
        prod_type = metadata["product_type_name"]

        if prod_type in ("Validation Results", "Photo-z Table"):
            msg = f"does not support non-tabular data\n{FONTCOLORERR}"
            msg += "The method get_product() only supports simple tabular "
            msg += "data (product types: Spec-z Catalog, Training Set). "
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
                if fmt == "astropy":
                    return Table.from_pandas(dataframe)
                if fmt == "pandas":
                    return dataframe
                results = self.__transform_df(dataframe, metadata)
            else:
                if fmt == "astropy":
                    return tables_io.read(file_path, tType=tables_io.types.AP_TABLE)
                dataframe = tables_io.read(
                    file_path, tType=tables_io.types.PD_DATAFRAME
                )
                if fmt == "pandas":
                    return dataframe
                results = self.__transform_df(dataframe, metadata)

        print("Done!")
        return results

    def __transform_df(self, dataframe, metadata):
        """
        Transforms the dataframe into an object corresponding to
        its product type (currently we have two: Spec-z Catalog or
        Training Set) or returns the dataframe.

        Args:
            dataframe (pandas.DataFrame): dataframe
            metadata (dict): product metadata
        """

        metadata_df = self.display_product_metadata(metadata["id"], show=False)

        if metadata["product_type_name"] == "Spec-z Catalog":
            results = SpeczCatalog(dataframe, metadata, metadata_df)
        elif metadata["product_type_name"] == "Training Set":
            results = TrainingSet(dataframe, metadata, metadata_df)
        else:
            results = dataframe

        return results

    # ---- Training Set Maker methods ----#
    def combine_specz_catalogs(self, catalog_list, duplicates_critera="smallest flag"):
        """_summary_

        Args:
            catalog_list (_type_): _description_
            duplicates_critera (str, optional): _description_. Defaults to "smallest flag".

        Raises:
            NotImplementedError: _description_
        """
        # criteria: smallest flag, smallest error
        # newest survey
        # show progress bar
        # return SpeczCatalog object
        raise NotImplementedError

    def make_training_set(
        self,
        specz_catalog=None,
        photo_catalog=None,
        search_radius=1.0,
        multiple_match_criteria="select closest",
    ):
        """_summary_

        Args:
            specz_catalog (_type_, optional): _description_. Defaults to None.
            photo_catalog (_type_, optional): _description_. Defaults to None.
            search_radius (float, optional): _description_. Defaults to 1.0.
            multiple_match_criteria (str, optional): _description_. Defaults to "select closest".

        Raises:
            NotImplementedError: _description_
        """
        # "select closest"
        # keep all
        # show progress bar
        # return
        raise NotImplementedError
