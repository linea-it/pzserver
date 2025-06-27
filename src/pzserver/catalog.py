"""
Classes responsible for loading the datasets (products) of the Pz Server app
"""

import matplotlib.pyplot as plt
from IPython.display import display


class Catalog:
    """
    Main class for loading catalog
    """

    def __init__(self, data=None, metadata=None, metadata_df=None):
        """
        Catalog class constructor
        """

        self.data = data
        self.metadata = metadata
        self.metadata_df = metadata_df
        self.columns = metadata.get("main_file").get("columns_association")

    def display_metadata(self):
        """
        Displays the catalog's metadata

        Displays a pandas.io.formats.style.Styler object
        with the metadata informed by the product owner
        (optimized for use in Jupyter Notebook).

        """
        display(self.metadata_df.style.hide(axis="index"))


class SpeczCatalog(Catalog):
    """
    SpeczCatalog

    Args:
        Catalog (_type_): _description_
    """

    def plot(self, savefig=False):
        """
        Very basic plots to characterize a Redshift catalog.

        Args:
            savefig: option to save PNG figure (boolean)
        """

        ra_name = dec_name = redshift_name = None

        for col in self.columns:
            if col["ucd"] == "pos.eq.ra;meta.main":
                ra_name = col["column_name"]
            if col["ucd"] == "pos.eq.dec;meta.main":
                dec_name = col["column_name"]
            if col["ucd"] == "src.redshift":
                redshift_name = col["column_name"]

        if None in (ra_name, dec_name, redshift_name):
            print("Error: Values unknown")
            print(f"RA: {ra_name}, Dec: {dec_name}, Redshift: {redshift_name}")
            return None

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

        return None


class TrainingSet(Catalog):
    """
    TrainingSet

    Args:
        Catalog (_type_): _description_
    """

    def plot(self, mag_name=None, savefig=False):
        """Very basic plots to characterize a Training Set.

        Args:
            savefig: option to save PNG figure (boolean)
        """

        redshift_name = None

        for col in self.columns:
            if col["ucd"] == "src.redshift":
                redshift_name = col["column_name"]

        if not redshift_name:
            print("Error: Redshift unknown")
            print(f"Redshift: {redshift_name}")
            return None

        redshift_min = self.data[redshift_name].min() - 0.1
        if self.data[redshift_name].min() <= 0.1:
            redshift_min = 0.0

        redshift_max = self.data[redshift_name].max() + 0.1
        if self.data[redshift_name].max() > 10.0:
            redshift_max = 10.0

        if mag_name is None:
            plt.hist(self.data[redshift_name], bins=30, histtype="bar")
            plt.xlabel(redshift_name)
            plt.ylabel("counts")
            plt.xlim(redshift_min, redshift_max)
            plt.tight_layout()
        else:
            mag_min = self.data[mag_name].min() - 0.2
            if self.data[mag_name].min() < 16.0:
                mag_min = 16.0
            mag_max = self.data[mag_name].max() + 0.2
            if self.data[mag_name].max() > 30.0:
                mag_max = 28.0

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
            plt.plot(self.data[redshift_name], self.data[mag_name], ".")
            plt.xlabel(redshift_name)
            plt.ylabel(mag_name)
            plt.xlim(redshift_min, redshift_max)
            plt.ylim(mag_min, mag_max)

            plt.tight_layout()

        if savefig:
            filename = "train_set.png"
            plt.savefig(filename)
            return filename

        return None
