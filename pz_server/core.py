import requests

import numpy as np
#import scipy as sp
import pandas as pd
import matplotlib.pyplot as plt
#import seaborn as sns

class PzServer():

    def __init__(self, user, password):
        # to do: get user's github credentials for authentication
        # session = requests.Session()
        # session.auth = (user, password)
        pass

    def list_product_types(self):
        """Fetches the list of valid product types. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of valid product 
        types and their respective short description.
        
        Returns:
            A dict mapping product type names to the 
            corresponding description. 
        """ 

        raise NotImplementedError

    def list_users(self):
        """Fetches the list of registered users. 

        Connects to the Photo-z Server's admnistrative 
        database and fetches the list of registered 
        users (github username). 
        
        Returns:
            A list of github usernames.             
        """ 

        raise NotImplementedError

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

        raise NotImplementedError
