from curses.ascii import controlnames
import requests
#from IPython.display import Markdown
import numpy as np
#import scipy as sp
import pandas as pd
import matplotlib.pyplot as plt
#import seaborn as sns
from .api import PzServerApi


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
                    columns=["name", "display_name", "description"])

        return dataframe

    def list_users(self):
        """Fetches the list of registered users. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of registered 
        users (github username). 

        Returns:
            A list of github usernames.             
        """

        product_types_dict = self.api.get_all("users")
        dataframe = pd.DataFrame(product_types_dict, 
                    columns=["username", "last_name"])
        dataframe.rename(columns={"last_name": "user"}, inplace=True)
            
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

        items = self.api.get_all("releases")
        dataframe = pd.DataFrame(items)

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

        items = self.api.get_all("products")
        dataframe = pd.DataFrame(items)

        return dataframe

    def get_product_metadata(self, product_id=None):
        """Fetches the product metadata. 

        Connects to the Photo-z Server's database and 
        fetches the metadata available for a given 
        data product located by product_id (provided 
        as argumetn by the user). 

        Returns:
            A dict with data product metadata informed
            py the product owner. 
        """
        raise NotImplementedError

    def get_product(self, product_id=None):
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
        return self.api.get("products", product_id)
