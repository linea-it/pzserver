#from imp import acquire_lock
import pandas as pd
from IPython.display import display
#from .api import PzServerApi
import tables_io
pd.options.display.max_colwidth = None
#pd.options.display.max_rows = 6


class SpeczSample():

    def __init__(self):
        """ SpeczSample class constructor  """
        
    def specz_combine(self, specz_catalog_list, duplicates_criteria="" ):
        """Fetches the list of valid product types.

        Connects to the Photo-z Server's administrative
        database and fetches the list of valid product
        types and their respective short description.

        Returns:
            dict of product types
        """
        return self.api.get_all("product-types")
