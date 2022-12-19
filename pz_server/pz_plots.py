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

def train_set_plots(training_set,
                    savefig=False,
                    redshift_name="redshift", 
                    mag_name="mag_i_cModel"):

    if training_set[mag_name].min() < 16.:
        mag_min = 16.
    else: 
        mag_min = training_set[mag_name].min() - 0.2
    if training_set[mag_name].max() > 30.:
        mag_max = 28.
    else: 
        mag_max = training_set[mag_name].max() + 0.2

    if training_set[redshift_name].min() <= 0.1:
            redshift_min = 0.
    else: 
        redshift_min = training_set[redshift_name].min() - 0.1
    if training_set[redshift_name].max() > 10.:
        redshift_max = 10.
    else: 
        redshift_max = training_set[redshift_name].max() + 0.1
    
    
    plt.figure(figsize=[12,4])
    plt.subplot(131)
    plt.hist(training_set[mag_name], bins=30, histtype="bar")
    plt.xlabel(mag_name)
    plt.xlim(mag_min, mag_max)
    
    plt.subplot(132)
    plt.hist(training_set[redshift_name], bins=30, histtype="bar")
    plt.xlabel(redshift_name)
    plt.xlim(redshift_min, redshift_max)
    
    plt.subplot(133)
    plt.plot(training_set[redshift_name], training_set[mag_name], '.')
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






