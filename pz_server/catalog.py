import pandas as pd
import matplotlib.pyplot as plt


class SpeczCatalog(pd.DataFrame):
    
     
    #def __init__(self, data=None, product_id=None):
    #    self.product_id = product_id
        #self.data = data_dict
        #print(len(data)) 
     #   pd.DataFrame.__init__(self)#data=data)
     #   self.data=data 
        #self.attrs["product_id"] = product_id 
        #atalog.__init__(product_id, dataframe)
    #    print("2")

    def plot(self, savefig=False, 
                ra_name="ra",
                dec_name="dec",
                redshift_name="redshift"):
        """ Basic plots to characterize a Spec-z catalog. 

        Args: 
            savefig: option to save PNG figure (boolean)

        """

        plt.figure(figsize=[9,4])
        plt.subplot(121)
        #plt.hist2d(dataframe[ra_name], dataframe[dec_name], bins=[100,100])
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


class TrainingSet: 
    def __init__(self): #f, product_id=None):
        pass #     super().__init__(product_id)

    
#     def plot(self):
#         raise NotImplementedError 


