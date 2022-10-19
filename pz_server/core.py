from asyncio import DatagramProtocol
from curses.ascii import controlnames
import requests
import numpy as np
import pandas as pd
from IPython.display import display
import matplotlib.pyplot as plt
from .api import PzServerApi
import tables_io
pd.options.display.max_colwidth = None


class PzServer():

    def __init__(self, token=None, host="pz"):
        if token is None:
            raise ValueError("Please provide a valid token.")
        else:
            self.api = PzServerApi(token, host)

    def list_product_types(self, jupyter=True):
        """Fetches the list of valid product types. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of valid product 
        types and their respective short description.

        If called from a Jupyter notebbok, displays a 
        pandas.io.formats.style.Styler object mapping the 
        product type names to the corresponding descriptions.

        """
        results_dict = self.api.get_all("product-types")
        dataframe = pd.DataFrame(results_dict,
                                 columns=["display_name", "description"])
        dataframe.rename(
            columns={"display_name": "product_type"}, inplace=True)
        if jupyter:
            display(dataframe.style.hide(axis="index"))
        else:
            print(dataframe)

    def list_users(self, jupyter=True):
        """Fetches the list of registered users. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of registered 
        users (GitHub username). 

        If called from a Jupyter notebbok, displays a 
        pandas.io.formats.style.Styler object mapping 
        the users to corresponding GitHub usernames.             

        """

        results_dict = self.api.get_all("users")
        dataframe = pd.DataFrame(results_dict,
                                 columns=["username", "last_name"])
        dataframe.rename(columns={"last_name": "user"},
                         inplace=True)

        if jupyter:
            display(dataframe.style.hide(axis="index"))
        else:
            print(dataframe)


    def list_releases(self, jupyter=True):
        """Fetches the list of valid data releases. 

        Connects to the Photo-z Server's admnistrative
        database and fetches the list of valid LSST
        data releases corresponding to the data products
        available. The resulting list is expected to
        increase over the years of survey operations.

        If called from a Jupyter notebbok, displays a 
        pandas.io.formats.style.Styler object mapping 
        the data release tags to their full names.
        """

        results_dict = self.api.get_all("releases")
        dataframe = pd.DataFrame(results_dict,
                                 columns=["display_name", "description"])
        dataframe.rename(columns={"display_name": "release"},
                         inplace=True)

        if jupyter:
            display(dataframe.style.hide(axis="index"))
        else:
            print(dataframe)


    def list_products(self, filters=None, jupyter=True):
        """Fetches the list of data products available. 

        Connects to the Photo-z Server's database and 
        fetches the filtered list of data products 
        available. The (optional) filters are provided 
        as dictionary by the user as argument. Default 
        is no filter.  

        If called from a Jupyter notebbok, displays a 
        pandas.io.formats.style.Styler object with the 
        list of all products available with the metadata
        informed by the owners.

        Args:
            filters (dict): dictionary with strings (or a 
                            list of strings) patterns 
                            to filter the results. 

        """
        results_dict = self.api.get_products(filters)
        dataframe = pd.DataFrame(results_dict,
                                 columns=["id", "display_name",
                                          "product_type_name", "survey", "release_name",
                                          "uploaded_by", "official_product",  # "pz_code",
                                          "description", "created_at"])

        dataframe.rename(columns={"display_name": "product_name",
                                  "release_name": "release",
                                  "product_type_name": "product_type"},
                         inplace=True)

        if jupyter:
            display(dataframe.style.hide(axis="index"))
        else:
            print(dataframe)


    #--------------------------------------------------#

    def get_product_metadata(self, product_id=None, display_table=True):
        """Fetches the product metadata. 

        Connects to the Photo-z Server's database and 
        fetches the metadata available for a given 
        data product located by product_id (provided 
        as argumetn by the user). 

        Args:
            product_id (int): data product unique identifier 

            display_table (boolean): show as styled dataframe,
                                     default=True

        Returns:
            A Pandas DataFrame with data product metadata 
            informed by the product owner. 
        """

        results_dict = self.api.get("products", product_id)

        if display_table:
            columns = ["id", "display_name",
                       "product_type_name", "survey", "release_name",
                       "uploaded_by", "official_product",  # "pz_code",
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

        return results_dict

    def get_product(self, product_id=None, save_file_as=False):
        """Fetches the data to local. 

        Connects to the Photo-z Server's database and 
        fetches the data stored as registered data 
        product. The result depends on product type. 
        If tabular data, returns one of the types 
        supported by the Python package tables_io 
        (AP_TABLE, NUMPY_DICT, NUMPY_RECARRAY, 
        PD_DATAFRAME). If the data product is composed 
        of multiple files, it downloads a .tar file 
        to local environment and returns a string with 
        the file name. 

        Args:
            product_id (int): data product unique identifier 

            save_file_as (str/boolean): file name to save 
                                    the data, default=False

        Returns:
            Tabular object with data (default is Pandas 
            Dataframe) or .tar file (in case of multiple files). 
        """
        results_dict = self.api.get_content(product_id)
        dataframe = pd.DataFrame(results_dict)

        if save_file_as:
            tables_io_formats = ['fits', 'hf5', 'hdf5', 'fit', 'h5', 'pq']
            fmt = save_file_as.split('.')[-1]
            if fmt == "csv":
                dataframe.to_csv(save_file_as)
            elif fmt in tables_io_formats:
                tables_io.write(dataframe, save_file_as)
            else:
                raise ValueError("File format is not supported. \n"
                                 "Please provide a file name with one of the suffixes:\n"
                                 "['fits', 'hf5', 'hdf5', 'fit', 'h5', 'pq'] ")

        return dataframe
