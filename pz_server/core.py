from curses.ascii import controlnames
import requests
#from IPython.display import Markdown
import numpy as np
#import scipy as sp
import pandas as pd
import matplotlib.pyplot as plt
#import seaborn as sns
from .api import PzServerApi
from tomark import Tomark
from IPython.display import display_markdown


class PzServer():

    def __init__(self, token, host="pz"):
        # token
        self.api = PzServerApi(token, host)

    def list_product_types(self):
        """Fetches the list of valid product types. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of valid product 
        types and their respective short description.

        Returns:
            A Pandas DataFrame mapping product type names
            to the corresponding description.
        """

        product_types_dict = self.api.get_all("product-types")
        dataframe = pd.DataFrame(product_types_dict, 
                    columns=["display_name", "description"])
        dataframe.rename(columns={"display_name": "product type"}, inplace=True)


        return dataframe

    def list_users(self):
        """Fetches the list of registered users. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of registered 
        users (github username). 

        Returns:
            A list of github usernames.             
        """

        users_dict = self.api.get_all("users")
        dataframe = pd.DataFrame(users_dict, 
                    columns=["username", "last_name"])
        dataframe.rename(columns={"last_name": "user",
                "username": "user name"}, inplace=True)
            
        return dataframe

    def list_releases(self):
        """Fetches the list of valid data releases. 

        Connects to the Photo-z Server's admnistrative
        database and fetches the list of valid LSST
        data releases corresponding to the data products
        available. The result list is expected to
        increase over the years of survey operations.

        Returns:
            A list data release tags.
        """

        releases_dict = self.api.get_all("releases")
        dataframe = pd.DataFrame(releases_dict, 
                    columns=["display_name"])
        dataframe.rename(columns={"display_name": "release"}, 
                    inplace=True)
            
        return dataframe

    def list_products(self, filters=None):
        """Fetches the list of data products available. 

        Connects to the Photo-z Server's database and 
        fetches the filtered list of data products 
        available. The (optional) filters are provided 
        as dictionary by the user as argument. Default 
        is no filter.  

        Returns:
            A dict mapping data products to the corresponding 
            short description informed by the owners.             
        """

        products_dict = self.api.get_all("products")
        # dataframe = pd.DataFrame(products_dict, 
        #             columns=["id", "release", "uploaded_by",   
        #              "product_type", "official_product", 
        #              "survey", "pz_code", "description", "created_at"]
        dataframe = pd.DataFrame(products_dict, 
                    columns=["id", "release_name", "uploaded_by",   
                     "product_type_name", "official_product", 
                     "survey", "pz_code", "description", "created_at"])

        dataframe.rename(columns={"release_name": "release",
                                  "uploaded_by": "uploaded by", 
                                  "product_type_name": "product type",
                                  "official_product": "official product",
                                  "pz_code":  "pz code",
                                  "created_at": "created at"}, inplace=True)

        return dataframe

    def get_product_metadata(self, product_id=None, show_as_markdown=True):
        """Fetches the product metadata. 

        Connects to the Photo-z Server's database and 
        fetches the metadata available for a given 
        data product located by product_id (provided 
        as argumetn by the user). 

        Returns:
            A dict with data product metadata informed
            py the product owner. 
        """

        metadata_dict = self.api.get("products", product_id)
        if show_as_markdown:  
            transposed_list = []
            for k,v in metadata_dict.items():
                transposed_list.append({"key": k, "value": v})
            markdown = Tomark.table(transposed_list)
            display_markdown(markdown, raw=True) 
        
        return metadata_dict


    def get_product(self, product_id=None, save_file=False):
        """Fetches the data to local. 

        Connects to the Photo-z Server's database and 
        fetches the data stored as registered data 
        product. The result depend on product type. 
        If tabular data, returns Astropy Table. If 
        multiple files, download a .tar file to local
        environment and returns string with file name. 

        Returns:
            Astropy Table with tabular data or 
            .tar file (in case of multiple files). 
        """
        
        return self.api.get_content(product_id)
