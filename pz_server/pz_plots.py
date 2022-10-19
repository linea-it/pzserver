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
    plt.hist(dataframe[redshift_name], bins=30, histtype="bar")
    plt.xlabel("redshift")
    plt.ylabel("counts")
    plt.tight_layout()

    if savefig:
        filename = "specz_catalog.png"
        plt.savefig(filename)
        return filename
    else:
        pass

def train_valid_plots(train=None, valid=None, 
                    savefig=False,
                    redshift_name="redshift", 
                    mag_name="mag_i_cModel"):

    if train[mag_name].min() < 16.:
        mag_min = 16.
    else: 
        mag_min = train[mag_name].min() - 0.2
    if train[mag_name].max() > 30.:
        mag_max = 28.
    else: 
        mag_max = train[mag_name].max() + 0.2

    if train[redshift_name].min() <= 0.1:
            redshift_min = 0.
    else: 
        redshift_min = train[redshift_name].min() - 0.1
    if train[redshift_name].max() > 10.:
        redshift_max = 10.
    else: 
        redshift_max = train[redshift_name].max() + 0.1
    
    
    plt.figure(figsize=[12,4])
    plt.subplot(131)
    if train is not None: 
        plt.hist(train[mag_name], label="train", 
                 bins=30, histtype="bar")
    if valid is not None: 
        plt.hist(valid[mag_name], label="valid", 
                 bins=30, histtype="step", lw=2)
    plt.legend(loc="upper left")
    plt.xlabel(mag_name)
    plt.xlim(mag_min, mag_max)
    
    plt.subplot(132)
    if train is not None: 
        plt.hist(train[redshift_name], label="train", 
                 bins=30, histtype="bar")
    if valid is not None: 
        plt.hist(valid[redshift_name], label="valid", 
                 bins=30, histtype="step", lw=2)
    #plt.legend()
    plt.xlabel(redshift_name)
    plt.xlim(redshift_min, redshift_max)
    
    plt.subplot(133)
    if train is not None: 
        plt.plot(train[redshift_name], train[mag_name],
                 '.', label="train")
    if valid is not None: 
        plt.plot(valid[redshift_name], valid[mag_name],
                 '.', label="valid")
    plt.legend()
    plt.xlabel(redshift_name)
    plt.ylabel(mag_name)   
    plt.xlim(redshift_min, redshift_max)
    plt.ylim(mag_min, mag_max)

    plt.tight_layout()

    if savefig:
        filename = "train_valid_set.png"
        plt.savefig(filename)
        return filename
    else:
        pass






