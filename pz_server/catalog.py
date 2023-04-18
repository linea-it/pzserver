import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
# import warnings
# warnings.filterwarnings('ignore')


class Catalog: 
    
    def __init__(self, data=None, metadata=None): 
        self.data = pd.DataFrame(data)
        self.metadata = metadata
        self.columns = metadata.get("main_file").get("columns_association")

    
    def display_metadata(self):
        # TBD: this method is duplicate with other from core.py, need refactoring  
        columns = ["id", "internal_name", "display_name",
                   "product_type_name", "survey", "release_name",
                   "uploaded_by", "official_product",  "pz_code",
                   "description", "created_at", "main_file"]
        transposed_list = []
        for k, v in self.metadata.items():
            if k in columns:
                if k == "release_name":
                    k = "release"
                if k == "product_type_name":
                    k = "product_type"
                if k == "display_name":
                    k = "product_name"
                if k == "main_file": 
                    v = v['name']
                transposed_list.append({"key": k, "value": v})
        dataframe = pd.DataFrame(transposed_list)
        display(dataframe.style.hide(axis="index"))
    
    def plot(self):
        raise NotImplemented

    

class SpeczCatalog(Catalog):

    def __init__(self, data=None, metadata=None): 
        super().__init__(data, metadata)
    
        
    def plot(self, savefig=False):
        """ Very basic plots to characterize a Spec-z catalog.

        Args:
            savefig: option to save PNG figure (boolean)
        
        """
        for col in self.columns: 
            if col["ucd"] == "pos.eq.ra;meta.main":
                ra_name = col["column_name"]    
            if col["ucd"] == "pos.eq.dec;meta.main":
                dec_name = col["column_name"]         
            if col["ucd"] == "src.redshift":
                redshift_name = col["column_name"] 
        plt.figure(figsize=[8, 3])
        plt.subplot(121)
        plt.scatter(self.data[ra_name], self.data[dec_name])
        plt.xlabel(f"{ra_name} (deg)")
        plt.ylabel(f"{dec_name} (deg)")
        plt.subplot(122)
        plt.hist(self.data[redshift_name], bins=30, histtype="bar")
        plt.xlabel(redshift_name)
        plt.ylabel("counts")
        plt.tight_layout()

        if savefig:
            filename = "specz_catalog.png"
            plt.savefig(filename)
            return filename
        else:
            pass


class TrainingSet(Catalog):
    
    def __init__(self, data=None, metadata=None): 
        super().__init__(data, metadata)

    def plot(self, mag_name = None, savefig=False):

        """ Very basic plots to characterize a Training Set.

        Args:
            savefig: option to save PNG figure (boolean)
        """
        for col in self.columns:           
            if col["ucd"] == "src.redshift":
                redshift_name = col["column_name"] 

        if self.data[redshift_name].min() <= 0.1:
            redshift_min = 0.
        else:
            redshift_min = self.data[redshift_name].min() - 0.1
        if self.data[redshift_name].max() > 10.:
            redshift_max = 10.
        else:
            redshift_max = self.data[redshift_name].max() + 0.1

        if mag_name is None: 
            plt.hist(self.data[redshift_name], bins=30, histtype="bar")
            plt.xlabel(redshift_name)
            plt.ylabel("counts")
            plt.xlim(redshift_min, redshift_max)
            plt.tight_layout()
        else: 
            if self.data[mag_name].min() < 16.:
                mag_min = 16.
            else:
                mag_min = self.data[mag_name].min() - 0.2
            if self.data[mag_name].max() > 30.:
                mag_max = 28.
            else:
                mag_max = self.data[mag_name].max() + 0.2
                
            plt.figure(figsize=[12, 4])
            plt.subplot(131)
            plt.hist(self.data[mag_name], bins=30, histtype="bar")
            plt.xlabel(mag_name)
            plt.ylabel("counts")
            plt.xlim(mag_min, mag_max)

            plt.subplot(132)
            plt.hist(self.data[redshift_name], bins=30, histtype="bar")
            plt.xlabel(redshift_name)
            plt.ylabel("counts")
            plt.xlim(redshift_min, redshift_max)

            plt.subplot(133)
            plt.plot(self.data[redshift_name], self.data[mag_name], '.')
            plt.xlabel(redshift_name)
            plt.ylabel(mag_name)
            plt.xlim(redshift_min, redshift_max)
            plt.ylim(mag_min, mag_max)

            plt.tight_layout()

        if savefig:
            filename = "train_set.png"
            plt.savefig(filename)
            return filename
        else:
            pass
