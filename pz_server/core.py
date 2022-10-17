from asyncio import DatagramProtocol
from curses.ascii import controlnames
import requests
import numpy as np
import pandas as pd
pd.options.display.max_colwidth = None

import matplotlib.pyplot as plt
from .api import PzServerApi
import tables_io


class PzServer():

    def __init__(self, token=None, host="pz"):
        if token is None:
            raise ValueError("Please provide a valid token.")
        else:
            self.api = PzServerApi(token, host)

    def list_product_types(self):
        """Fetches the list of valid product types. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of valid product 
        types and their respective short description.

        Returns:
            A Pandas DataFrame mapping product type names
            to the corresponding descriptions.
        """
        results_dict = self.api.get_all("product-types")
        dataframe = pd.DataFrame(results_dict, 
                    columns=["display_name", "description"])          
        dataframe.rename(columns={"display_name": "product_type"}, inplace=True)
        
        return dataframe.style.hide(axis="index")

    def list_users(self):
        """Fetches the list of registered users. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of registered 
        users (GitHub username). 

        Returns:
            A Pandas DataFrame with GitHub usernames.             
        """

        results_dict = self.api.get_all("users")
        dataframe = pd.DataFrame(results_dict, 
                    columns=["last_name", "username"])
        dataframe.rename(columns={"last_name": "user"}, 
                    inplace=True)
            
        return dataframe.style.hide(axis="index")

    def list_releases(self):
        """Fetches the list of valid data releases. 

        Connects to the Photo-z Server's admnistrative
        database and fetches the list of valid LSST
        data releases corresponding to the data products
        available. The resulting list is expected to
        increase over the years of survey operations.

        Returns:
            A Pandas DataFrame with data release tags.
        """

        results_dict = self.api.get_all("releases")
        dataframe = pd.DataFrame(results_dict, 
                    columns=["display_name", "description"])
        dataframe.rename(columns={"display_name": "release"}, 
                    inplace=True)
            
        return dataframe.style.hide(axis="index")

    def list_products(self, filters=None):
        """Fetches the list of data products available. 

        Connects to the Photo-z Server's database and 
        fetches the filtered list of data products 
        available. The (optional) filters are provided 
        as dictionary by the user as argument. Default 
        is no filter.  

        Returns:`
            A Pandas DataFrame mapping data products to 
            the corresponding short description informed 
            by the owners.             
        """

        results_dict = self.api.get_all("products")
        dataframe = pd.DataFrame(results_dict, 
                    columns=["id", "release_name", "uploaded_by",   
                     "product_type_name", "official_product", 
                     "survey", "pz_code", "description", "created_at"])
        dataframe.rename(columns={"release_name": "release",
                                  "product_type_name": "product_type"},                  
                        inplace=True)
        return dataframe.style.hide(axis="index")

    def get_product_metadata(self, product_id=None):
        """Fetches the product metadata. 

        Connects to the Photo-z Server's database and 
        fetches the metadata available for a given 
        data product located by product_id (provided 
        as argumetn by the user). 

        Returns:
            A Pandas DataFrame with data product metadata 
            informed by the product owner. 
        """

        results_dict = self.api.get("products", product_id)
        columns=["id", "release_name", "product_type_name", "uploaded_by",
            "display_name", "official_product", "survey", "pz_code", 
            "description", "created_at"]
        transposed_list = []
        for k,v in results_dict.items():
            if k in columns: 
                transposed_list.append({"key": k, "value": v})
            
        dataframe = pd.DataFrame(transposed_list).style.hide(axis="index")
        dataframe.replace("release_name", "release")
        # dataframe.replace("product_type_name", "product_type")
        # dataframe.replace("display_name", "product_name")

        return dataframe 
       

    def get_product(self, product_id=None, save_file=False, tabletype=tables_io.types.PD_DATAFRAME):
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

        Returns:
            Tabular object with data (default is Pandas 
            Dataframe) or .tar file (in case of multiple files). 
        """
        
        results_dict = self.api.get_content(product_id)
        #transposed_list = []
        #for k,v in results_dict.items():
            #transposed_list.append({"key": k, "value": v})
        #dataframe = pd.DataFrame(transposed_list) 

        dataframe = pd.DataFrame(results_dict) 
        return dataframe 

        #return results_dict 
