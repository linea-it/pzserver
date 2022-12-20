import pandas as pd
from .api import PzServerApi
#from core import PzServer


class TabularDataProduct(pd.DataFrame):
    def __init__(self, prod_id=None):
        """ TabularDataProduct class constructor"""    
        pd.DataFrame.__init__(self)
        self.prod_id = prod_id

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

class SpeczCatalog(pd.DataFrame):
