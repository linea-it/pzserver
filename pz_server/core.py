from .catalog import Catalog, SpeczCatalog, TrainingSet
import pandas as pd
from IPython.display import display
from .api import PzServerApi
# import tables_io
pd.options.display.max_colwidth = None
pd.options.display.max_columns = 500
pd.options.display.max_rows = 6


class PzServer:

    def __init__(self, token=None, host="pz"):
        """ PzServer class constructor
        Args:
            host (str): "pz" (production) or
                        "pz-dev" (test environment) or
                        "localhost" (dev environment) or
                        "api url" 
        """
        if token is None:
            raise ValueError("Please provide a valid token.")
        else:
            self.api = PzServerApi(token, host)
        self._token = token

    def get_product_types(self):
        """Fetches the list of valid product types.

        Connects to the Photo-z Server's administrative
        database and fetches the list of valid product
        types and their respective short description.

        Returns:
            dict of product types
        """
        return self.api.get_all("product-types")

    def display_product_types(self):
        """Displays the list of product types as dataframe

        Displays a pandas.io.formats.style.Styler object
        mapping the product type names to the corresponding
        descriptions (optimized for use in Jupyter Notebook).
        """
        results_dict = self.get_product_types()
        dataframe = pd.DataFrame(results_dict,
                                 columns=["display_name", "description"])
        dataframe.rename(
            columns={"display_name": "Product type",
                     "description": "Description"}, inplace=True)
        display(dataframe.style.hide(axis="index"))

    def get_users(self):
        """Fetches the list of registered users.

        Connects to the Photo-z Server's administrative
        database and fetches the list of registered
        users (first/last name and GitHub username).

        Returns:
            dict of users
        """
        return self.api.get_all("users")

    def display_users(self):
        """Displays the list of users as dataframe

        Displays a pandas.io.formats.style.Styler object
        mapping the users to corresponding GitHub usernames
        (optimized for use in Jupyter Notebook).
        """
        results_dict = self.get_users()
        dataframe = pd.DataFrame(results_dict,
                                 columns=["username", "last_name"])
        dataframe.rename(columns={"username": "GitHub username",
                                  "last_name": "name"},
                         inplace=True)
        display(dataframe.style.hide(axis="index"))

    def get_releases(self):
        """Fetches the list of valid data releases.

        Connects to the Photo-z Server's administrative
        database and fetches the list of valid LSST
        data releases corresponding to the data products
        available. The resulting list is expected to
        increase over the years of survey operations.

        Returns:
            dict of releases
        """
        return self.api.get_all("releases")

    def display_releases(self):
        """Displays the list of data releases as dataframe

        Displays a pandas.io.formats.style.Styler object
        mapping the the data release tags to their full
        names (optimized for use in Jupyter Notebook).
        """
        results_dict = self.api.get_all("releases")
        dataframe = pd.DataFrame(results_dict,
                                 columns=["display_name", "description"])
        dataframe.rename(columns={"display_name": "Release",
                                  "description": "Description"}, inplace=True)
        display(dataframe.style.hide(axis="index"))

    def get_products_list(self, filters=None):
        """Fetches the list of data products available.

        Connects to the Photo-z Server's database and
        fetches the filtered list of data products
        available.

        Args:
            filters (dict): dictionary with strings
                (or a list of strings) patterns to
                filter the results.

        Returns:
            dict of data products
        """
        return self.api.get_products(filters)

    def display_products_list(self, filters=None):
        """Displays the list of data products as dataframe

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
        dataframe = pd.DataFrame(results_dict,
                                 columns=["id", "internal_name", "display_name",
                                          "product_type_name", "survey", "release_name",
                                          "uploaded_by", "official_product",  # "pz_code",
                                          "description", "created_at"])

        dataframe.rename(columns={"display_name": "product_name",
                                  "release_name": "release",
                                  "product_type_name": "product_type"},
                         inplace=True)
        display(dataframe.style.hide(axis="index"))

    def get_product_metadata(self, product_id=None):
        """Fetches the product metadata.

        Connects to the Photo-z Server's database and
        fetches the metadata informed by the product
        owner.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal name)

        Returns:
            dict of metadata
        """
        product_id = str(product_id)
        if "_" in product_id:
            list = self.api.get_products({"internal_name": product_id})
            return list[0]
        else:
            return self.api.get("products", product_id)

    def display_product_metadata(self, product_id=None):
        """Displays the metadata informed by the product owner.

        Displays a pandas.io.formats.style.Styler object
        with the metadata informed by the product owner
        (optimized for use in Jupyter Notebook).

        Args:
            product (str or int): data product
                unique identifier (product id
                number or internal name)
        """

        results_dict = self.get_product_metadata(product_id)

        columns = ["id", "internal_name", "display_name",
                   "product_type_name", "survey", "release_name",
                   "uploaded_by", "official_product",  "pz_code",
                   "description", "created_at"]
        transposed_list = []
        for k, v in results_dict.items():
            if k in columns:
                if k == "release_name":
                    k = "release"
                if k == "product_type_name":
                    k = "product_type"
                if k == "display_name":
                    k = "product_name"
                transposed_list.append({"key": k, "value": v})
        dataframe = pd.DataFrame(transposed_list)
        display(dataframe.style.hide(axis="index"))

    def download_product(self, product_id=None, save_in="."):
        """Download the data to local. 

        Connects to the Photo-z Server's database and 
        download a compressed zip file containing all 
        the data and metadata of a given data product.

        Args:
            product_id (str or int): data product 
                unique identifier (product id 
                number or internal name)
            save_in (str): location where the file will 
                be saved

        """
        data = self.api.download_product(product_id, save_in)
        if data.get("success", False):
            print(f"File saved as: {data['message']}")
        else:
            print(f"Error: {data['message']}")

    def get_product(self, product_id=None):
        """Fetches the data to local.

        Connects to the Photo-z Server's database and
        fetches the tabular data stored as registered 
        data product.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal name)

        Returns:
            Catalog (child class from dict)

        """

        prod_type = self.get_product_metadata(product_id)['product_type_name']
        print(prod_type)

        if (prod_type == "Validation Results" or prod_type == "Photo-z Table"):
            print("\033[38;2;{};{};{}m{} ".format(255, 0, 0, "WARNING:"))
            print("The method get_product() only supports simple tabular ")
            print("data (product types: Spec-z Catalog, Training Set).")
            print(f"For {prod_type}, please use method download_product().")
        else:
            results_dict = self.api.download_main_file(product_id)
            return results_dict

            # metadata = self.get_product_metadata(product_id)

            # if prod_type == "Spec-z Catalog" or prod_type == "Training Set":
            #     catalog = Catalog(results_dict)
            # else:
            #     raise ValueError("Unknown product type")

            # return catalog

    def get_specz_catalog(self, product_id=None):
        """Fetches Spec-z Catalog to local.

        Connects to the Photo-z Server's database and
        fetches the data stored as registered data
        product. Particular for product type equals
        Spec-z Catalog.

        Args:
            product_id (str or int): data product
                unique identifier (product id
                number or internal name)

        Returns:
            SpeczCatalog (child class from pandas.DataFrame)

        """

        prod_type = self.get_product_metadata(product_id)['product_type_name']

        if prod_type != "Spec-z Catalog":
            print("\033[38;2;{};{};{}m{} ".format(255, 0, 0, "ERROR:"))
            print(f"The product {product_id} is not a Spec-z Catalog.")
            if prod_type == "Training Set":
                print("Please use the method get_train_set")
            elif (prod_type == "Validation Results" or prod_type == "Photo-z Table"):
                print("\033[38;2;{};{};{}m{} ".format(255, 0, 0, "WARNING:"))
                print("The methods get_...() only supports simple tabular ")
                print("data (product types: Spec-z Catalog, Training Set).")
                print(f"For {prod_type}, please use method download_product().")
        else:
            results_dict = self.api.get_content(product_id)
            metadata = self.get_product_metadata(product_id)

            catalog = SpeczCatalog(results_dict, metadata)

        return catalog

    def combine_specz_catalogs(self, catalog_list,
                               duplicates_criteria="smallest flag"):
        # smallest flag
        # smallest error
        # newest survey
        # show progress bar
        raise NotImplementedError

    def make_training_set(self, specz_catalog=None,
                          photo_catalog=None,
                          search_radius=1.0,
                          multiple_match_criteria="select closest"):
        # "select closest"
        # keep all
        # show progress bar
        raise NotImplementedError
