#from tkinter.messagebox import NO
#import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#import seaborn as sns


def specz_plots(dataframe, savefig=False, 
                ra_name="ra",
                dec_name="dec",
                redshift_name="redshift"):
    """ 
    Basic plots to characterize a Spec-z catalog. 

    Args: 
        dataframe: Input data (Pandas DataFrame)
        savefig: option to save PNG figure (boolean)

    """

    plt.figure(figsize=[9,4])
    plt.subplot(121)
    #plt.hist2d(dataframe[ra_name], dataframe[dec_name], bins=[100,100])
    plt.scatter(dataframe[ra_name], dataframe[dec_name])
    plt.xlabel("R.A. (deg)")
    plt.ylabel("Dec. (deg)")
    plt.subplot(122)
    plt.hist(dataframe[redshift_name], bins=30)
    plt.xlabel("redshift")
    plt.ylabel("counts")
    plt.tight_layout()

    if savefig:
        filename = "specz_catalog.png"
        plt.savefig(filename)
        return filename
    else:
        pass

def train_valid_plots(train=None, Valid=None, 
                    savefig=False,
                    redshift_name="z", 
                    mag_name="mag_cModel_i"):

    plt.figure(figsize=[12,4])
    plt.subplot(131)
    if train is not None: 
        plt.hist(train[mag_name], label="train")
    if valid is not None: 
        plt.hist(valid[mag_name], label="valid")
    plt.legend()
    plt.xlabel(f"magnitude {mag_name}")
    plt.subplot(132)
    if train is not None: 
        plt.hist(train[redshift_name], label="train")
    if valid is not None: 
        plt.hist(valid[redshift_name], label="valid")
    plt.legend()
    plt.xlabel("redshift")
    plt.subplot(133)
    if train is not None: 
        plt.plot(train[redshift_name], train[mag_name], label="train")
    if valid is not None: 
        plt.plot(train[redshift_name], train[mag_name], label="valid")
    plt.legend()
    plt.xlabel("redshift")
    plt.ylabel(mag_name)    
    plt.subplots_adjust()

    if savefig:
        filename = "train_valid_set.png"
        plt.savefig(filename)
        return filename
    else:
        pass






