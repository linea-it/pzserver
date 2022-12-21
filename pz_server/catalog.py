import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
# import warnings
# warnings.filterwarnings('ignore')


class SpeczCatalog(pd.DataFrame):

    def __init__(self, data=None, metadata=None):
        super().__init__(data)
        for key, value in metadata.items():
            self.attrs[key] = value

    @property
    def metadata(self):
        return self.attrs

    def display_metadata(self):
        columns = ["id", "internal_name", "display_name",
                   "product_type_name", "survey", "release_name",
                   "uploaded_by", "official_product",  "pz_code",
                   "description", "created_at"]
        transposed_list = []
        for k, v in self.metadata.items():
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

    def plot(self, savefig=False,
             ra_name="ra",
             dec_name="dec",
             redshift_name="redshift"):
        """ Basic plots to characterize a Spec-z catalog. 

        Args: 
            savefig: option to save PNG figure (boolean)

        """

        plt.figure(figsize=[9, 4])
        plt.subplot(121)
        # plt.hist2d(dataframe[ra_name], dataframe[dec_name], bins=[100,100])
        plt.scatter(self[ra_name], self[dec_name])
        plt.xlabel("R.A. (deg)")
        plt.ylabel("Dec. (deg)")
        plt.subplot(122)
        plt.hist(self[redshift_name], bins=30, histtype="bar")
        plt.xlabel("redshift")
        plt.ylabel("counts")
        plt.tight_layout()

        if savefig:
            filename = "specz_catalog.png"
            plt.savefig(filename)
            return filename
        else:
            pass


class TrainingSet(pd.DataFrame):

    def plot(self, savefig=False,
             redshift_name="redshift",
             mag_name="mag_i_cModel"):

        if self[mag_name].min() < 16.:
            mag_min = 16.
        else:
            mag_min = self[mag_name].min() - 0.2
        if self[mag_name].max() > 30.:
            mag_max = 28.
        else:
            mag_max = self[mag_name].max() + 0.2

        if self[redshift_name].min() <= 0.1:
            redshift_min = 0.
        else:
            redshift_min = self[redshift_name].min() - 0.1
        if self[redshift_name].max() > 10.:
            redshift_max = 10.
        else:
            redshift_max = self[redshift_name].max() + 0.1

        plt.figure(figsize=[12, 4])
        plt.subplot(131)
        plt.hist(self[mag_name], bins=30, histtype="bar")
        plt.xlabel(mag_name)
        plt.xlim(mag_min, mag_max)

        plt.subplot(132)
        plt.hist(self[redshift_name], bins=30, histtype="bar")
        plt.xlabel(redshift_name)
        plt.xlim(redshift_min, redshift_max)

        plt.subplot(133)
        plt.plot(self[redshift_name], self[mag_name], '.')
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
