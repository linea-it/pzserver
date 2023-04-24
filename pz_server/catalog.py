import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display 
# import warnings
# warnings.filterwarnings('ignore')


class Catalog: 
    
    def __init__(self, data=None, metadata=None, metadata_df=None): 
        """ Catalog class constructor """
        self.data = pd.DataFrame(data)
        self.metadata = metadata
        self.columns = metadata.get("main_file").get("columns_association")
        self.metadata_df = metadata_df 
    
    def display_metadata(self):
        """Displays the catalog's metadata 

        Displays a pandas.io.formats.style.Styler object
        with the metadata informed by the product owner
        (optimized for use in Jupyter Notebook).

        """
        display(self.metadata_df.style.hide(axis="index"))
    
    def plot(self):
        raise NotImplemented

    

class SpeczCatalog(Catalog):

    def __init__(self, data=None, metadata=None, metadata_df=None): 
        super().__init__(data, metadata, metadata_df)
    
        
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
    
    def __init__(self, data=None, metadata=None, metadata_df=None): 
        super().__init__(data, metadata, metadata_df)

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
