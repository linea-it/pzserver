Photo-z Server - Tutorial Notebook
==================================

Contact author: `Julia Gschwend <mailto:julia@linea.org.br>`__

Last verified run: 2024-Jan-23

.. raw:: html

   <div id="notebook-contents" />

Notebook contents
=================

-  PZ Server

   -  `Introduction <#introduction>`__
   -  `How to upload a data product to the PZ
      Server <#how-to-upload-a-data-product-to-the-pz-server>`__
   -  `How to download a data product from the PZ
      Server <#how-to-download-a-data-product-from-the-pz-server>`__

-  PZ Server API (Python library pz-server-lib)

   -  `How to get general info from PZ
      Server <#how-to-get-general-info-from-pz-server>`__
   -  `How to display the metadata of a data
      product <#how-to-display-the-metadata-of-a-data-product>`__
   -  `How to download data products as .zip
      files <#how-to-download-data-products-as-zip-files>`__
   -  `How to share data products with other RSP
      users <#how-to-share-data-products-with-other-rsp-users>`__
   -  `How to retrieve contents of data products (work on
      memory) <#how-to-retrieve-contents-of-data-products-work-on-memory>`__

-  Product types

   -  `Spec-z Catalogs <#spec-z-catalog>`__
   -  `Training Sets <#training-sets>`__
   -  `Photo-z Validation Results <#photo-z-validation-results>`__
   -  `Photo-z Tables <#photo-z-tables>`__

The PZ Server
=============

.. container::
   :name: introduction

Introduction
------------

The Photo-z (PZ) Server is an online service available for the LSST
Community to host and share lightweight photo-z related data products.
The upload and download of data and metadata can be done at the website
`pz-server.linea.org.br <https://pz-server.linea.org.br/>`__ (during the
development phase, a test environment is available at
`pz-server-dev.linea.org.br <https://pz-server-dev.linea.org.br/>`__).
There, you will find two separate pages containing a list of data
products each: one for LSST Data Management’s oficial data products, and
other for user-generated data products. **The registered data products
can also be accessed directly from Python code using the PZ Server’s
data access API, as demonstrated below.**

The PZ Server is developed and delivered as part of the in-kind
contribution program BRA-LIN, from LIneA to the Rubin Observatory’s
LSST. The service is hosted in the Brazilian IDAC, not directly
connected to the `Rubin Science Platform
(RSP) <https://data.lsst.cloud/>`__. However, it requires RSP
credentials for user’s authentication. For a comprehensive documentation
about the PZ Server, please visit the `PZ Server’s documentation
page <https://linea-it.github.io/pz-lsst-inkind-doc/>`__. There, you
will find also an overview of all LIneA’s contributions related to
Photo-zs. The internal documentation of the API functions is available
on the `API’s documentation
page <https://linea-it.github.io/pz-server-lib/html/index.html>`__.

.. container::
   :name: how-to-upload-a-data-product-to-the-pz-server

   `back to the top <#notebook-contents>`__

How to upload a data product to the PZ Server
---------------------------------------------

To upload a data product, click on the button **NEW PRODUCT** on the top
left of the **User-generated Data Products** page and fill in the Upload
Form with relevant metadata.

The photo-z-related products are organized into four categories (product
types):

-  **Spec-z Catalog:** Catalog of spectroscopic redshifts and positions
   (usually equatorial coordinates).
-  **Training Set:** Training set for photo-z algorithms (tabular data).
   It usually contains magnitudes, errors, and true redshifts.
-  **Photo-z Validation Results:** Results of a photo-z validation
   procedure (free format). Usually contains photo-z estimates (single
   estimates and/or pdf) of a validation set, photo-z validation
   metrics, validation plots, etc.
-  **Photo-z Table:** Results of a photo-z estimation procedure. Ideally
   in the same format as the photo-z tables delivered by the DM as part
   of the LSST data releases. If the data is larger than the file upload
   limit (200MB), the product entry stores only the metadata (and
   instructions on accessing the data should be provided in the
   description field).

.. container::

   `back to the top <#notebook-contents>`__

How to download a data product from the PZ Server
-------------------------------------------------

To download a data product available on the Photo-z Server, go to one of
the two pages by clicking on the card “LSST PZ Data Products” (for
official products released by LSST DM Team) or “User-generated Data
Products” (for products uploaded by the members of LSST community. The
download button is on the left side of each data product (each row of
the list).

.. container::
   :name: how-to-download-a-data-product-from-the-pz-server

   `back to the top <#notebook-contents>`__

The PZ Server API (Python library pz-server-lib)
================================================

Installation
------------

**Using pip**

The PZ Server API is avalialble on **pip** as ``pzserver``. To install
the API and its dependencies, type, on the Terminal:

::

   $ pip install pzserver 

**For developers**

Alternatively, if you have cloned the repository with:

::

   $ git clone https://github.com/linea-it/pzserver.git  

To install the API and its dependencies, type:

::

   $ pip install -e .
   $ pip install .[dev]

OBS: You might need to restart the kernel on the notebook to incorporate
the new library.

Imports and Setup
-----------------

.. code:: ipython3

    from pzserver import PzServer 
    import matplotlib.pyplot as plt
    %reload_ext autoreload 
    %autoreload 2

The connection with the PZ Server from Python code is done by an object
of the class ``PzServer``. To get authorization to define an instance of
``PzServer``, the users must provide an **API Token** generated on the
top right menu on the `PZ Server
website <https://pz-server.linea.org.br/>`__ (during the development
phase, on the `test
environment <https://pz-server-dev.linea.org.br/>`__).



.. code:: ipython3

    pz_server = PzServer(token="<your token>", host="pz-dev") # "pz-dev" is the temporary host for test phase  

.. container::
   :name: how-to-get-general-info-from-pz-server

   `back to the top <#notebook-contents>`__

How to get general info from PZ Server
--------------------------------------

The object ``pz_server`` just created above can provide access to data
and metadata stored in the PZ Server. It also brings useful methods for
users to navigate through the available contents. The methods with the
preffix ``get_`` return the result of a query on the PZ Server database
as a Python dictionary, and are most useful to be used programatically
(see detaials on the `API documentation
page <https://linea-it.github.io/pz-server-lib/html/index.html>`__).
Alternatively, those with the preffix ``display_`` show the results as a
styled `Pandas
DataFrames <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`__,
optimized for Jupyter Notebook (note: column names might change in the
display version). For instance:

Display the list of product types supported with a short description;

.. code:: ipython3

    pz_server.display_product_types()

Display the list of users who uploaded data products to the server;

.. code:: ipython3

    pz_server.display_users()

Display the list of data releases available at the time;

.. code:: ipython3

    pz_server.display_releases()

--------------

Display all data products available (WARNING: this list can rapdly grow
during the survey’s operation).

.. code:: ipython3

    pz_server.display_products_list() 

The information about product type, users, and releases shown above can
be used to filter the data products of interest for your search. For
that, the method ``list_products`` receives as argument a dictionary
mapping the products attributes to their values.

.. code:: ipython3

    pz_server.display_products_list(filters={"release": "LSST DP0", 
                                     "product_type": "Training Set"})

It also works if we type a string pattern that is part of the value. For
instance, just “DP0” instead of “LSST DP0”:

.. code:: ipython3

    pz_server.display_products_list(filters={"release": "DP0"})

It also allows the search for multiple strings by adding the suffix
``__or`` (two underscores + “or”) to the search key. For instance, to
get spec-z catalogs and training sets in the same search (notice that
filtering is not case sensitive):

.. code:: ipython3

    pz_server.display_products_list(filters={"product_type__or": ["Spec-z Catalog", "training set"]})

To fetch the results of a search and attribute to a variable, just
change the preffix ``display_`` by ``get_``, like this:

.. code:: ipython3

    search_results = pz_server.get_products_list(filters={"product_type": "results"}) # PZ Validation results
    search_results

.. container::
   :name: how-to-display-the-metadata-of-a-data-product

   `back to the top <#notebook-contents>`__

How to display the metadata of a data product
---------------------------------------------

The metadata of a given data product is the information provided by the
user on the upload form. This information is attached to the data
product contents and is available for consulting on the PZ Server page
or using this Python API (``pz-server-lib``).

All data products stored on PZ Server are identified by a unique **id**
number or an unique name, a *string* called **internal_name**, which is
created automatically at the moment of the upload by concatenating the
product **id** to the name given by its owner (replacing blank spaces by
"_", lowering cases, and removing special characters).

The ``PzServer``\ ’s method ``get_product_metadata()`` returns a
dictionary with the attibutes stored in the PZ Server about a given data
product identified by its **id** or **internal_name**. For use in a
Jupyter notebook, the equivalent ``display_product_metadata()`` shows
the results in a formated table.

.. code:: ipython3

    # pz_server.display_product_metadata(<id (int or str) or internal_name (str)>) 
    # pz_server.display_product_metadata(6) 
    # pz_server.display_product_metadata("6") 
    pz_server.display_product_metadata("6_simple_training_set") 

.. container::
   :name: how-to-download-data-products-as-zip-files

   `back to the top <#notebook-contents>`__

How to download data products as .zip files
-------------------------------------------

To download any data product stored in the PZ Server, use the
``PzServer``\ ’s method ``download_product`` informing the product’s
**internal_name** and the path to where it will be saved (the default is
the current folder). This method downloads a compressed .zip file which
contais all the files uploaded by the user, including data, anciliary
files and description files. The time spent to download a data product
depends on the internet connections between the user and the host. Let’s
try it with a small data product.

.. code:: ipython3

    pz_server.download_product(14, save_in=".")

.. container::
   :name: how-to-share-data-products-with-other-rsp-users

   `back to the top <#notebook-contents>`__

How to share data products with other RSP users
-----------------------------------------------

All data products uploaded to the PZ Server are imediately available and
visible to all PZ Server users (people with RSP credentials) through the
PZ Server website or via the API. Besides informing the product **id**
or **internal_name** for programatic access, another way to share a data
product is providing the product’s URL, which leads to the product’s
download page. The URL is composed by the PZ Server website address +
**/products/** + **internal_name**:

https://pz-server.linea.org.br/product/ + **internal_name**

or, if still in the development phase,

https://pz-server-dev.linea.org.br/product/ + **internal_name**

For example:

https://pz-server-dev.linea.org.br/product/6_simple_training_set

WARNING: The URL works only with the internal name, **not** with the
**id** number.

.. container::
   :name: how-to-retrieve-contents-of-data-products-work-on-memory

   `back to the top <#notebook-contents>`__

How to retrieve contents of data products (work on memory)
----------------------------------------------------------

Another feature of the PZ Server API is to let users retrieve the
contents of a given data product to work on memory (by atributing the
results of the method ``get_product()`` to a variable in the code). This
feature is available only for tabular data (product types: **Spec-z
Catalog** and **Training Set**).

By default, the method ``get_product`` returns an object from a
particular class, depending on the product’s type. The classes
``SpeczCatalog`` and ``TrainingSet`` are simple extensions of
``pandas.DataFrame`` (via class composition) with a couple of additional
attributes and methods, such as the attribute ``metadata``, and the
method ``display_metadata()``. Let’s see an example:

.. code:: ipython3

    catalog = pz_server.get_product(8)
    catalog

.. code:: ipython3

    catalog.display_metadata()

The tabular data is alocated in the attribute ``data``, which is a
``pandas.DataFrame``.

.. code:: ipython3

    catalog.data

.. code:: ipython3

    type(catalog.data)

It preserves the useful methods from ``pandas.DataFrame``, such as:

.. code:: ipython3

    catalog.data.info()

.. code:: ipython3

    catalog.data.describe()

In the prod-types you will see more details about these specific
classes. For those who prefer working with ``astropy.Table`` or pure
``pandas.DataFrame``, the method ``get_product()`` gives the flexibility
to choose the output format (``fmt="pandas"`` or ``fmt="astropy"``).

.. code:: ipython3

    dataframe = pz_server.get_product(8, fmt="pandas")
    print(type(dataframe))
    dataframe

.. code:: ipython3

    table = pz_server.get_product(8, fmt="astropy")
    print(type(table))
    table

--------------

Clean up

.. code:: ipython3

    del search_results, catalog, dataframe, table 

--------------

.. container::

   `back to the top <#notebook-contents>`__

Product types
=============

The PZ Server API provides Python classes with useful methods to handle
particular product types. Let’s recap the product types available:

.. code:: ipython3

    pz_server.display_product_types()

.. container::
   :name: spec-z-catalog

   `back to the top <#notebook-contents>`__

Spec-z Catalog
--------------

In the context of the PZ Server, Spec-z Catalogs are defined as any
catalog containing spherical equatorial coordinates and spectroscopic
redshift measurements (or, analogously, true redshifts from
simulations). A Spec-z Catalog can include data from a single
spectroscopic survey or a combination of data from several sources. To
be considered as a single Spec-z Catalog, the data should be provided as
a single file to PZ Server’s the upload tool. For multi-survey catalogs,
it is recommended to add the survey name or identification as an extra
column.

Mandatory columns: \* Right ascension [degrees] - ``float`` \*
Declination [degrees] - ``float`` \* Spectroscopic or true redshift -
``float``

Recommended columns: \* Spectroscopic redshift error - ``float`` \*
Quality flag - ``integer``, ``float``, or ``string`` \* Survey name
(recommended for compilations of data from different surveys)

Let’s see an example of Spec-z Catalog:

.. code:: ipython3

    gama = pz_server.get_product(14)

.. code:: ipython3

    gama.display_metadata()

Display basic statistics

.. code:: ipython3

    gama.data.describe()

The spec-z catalog object has a very basic plot method for quick
visualization of catalog properties

.. code:: ipython3

    gama.plot()

The attribute ``data``, which is a ``DataFrame`` preserves the ``plot``
method from Pandas.

.. code:: ipython3

    gama.data.plot(x="RA", y="DEC", kind="scatter")  

.. container::
   :name: training-sets

   `back to the top <#notebook-contents>`__

Training Sets
-------------

In the context of the PZ Server, Training Sets are defined as the
product of matching (spatially) a given Spec-z Catalog (single survey or
compilation) to the photometric data, in this case, the LSST Objects
Catalog. The PZ Server API offers a tool called *Training Set Maker* for
users to build customized Training Sets based on the Spec-z Catalogs
available. Please see the companion Jupyter Notebook
``pz_tsm_tutorial.ipynb`` for details.

*Note 1: Commonly the training set is split into two or more subsets for
photo-z validation purposes. If the Training Set owner has previously
defined which objects should belong to each subset (trainining and
validation/test sets), this information must be available as an extra
column in the table or as clear instructions for reproducing the subsets
separation in the data product description.*

*Note 2: The PZ Server only supports catalog-level Training Sets.
Image-based Training Sets, e.g., for deep-learning algorithms, are not
supported yet.*

Mandatory column: \* Spectroscopic (or true) redshift - ``float``

Other expected columns \* Object ID from LSST Objects Catalog -
``integer`` \* Observables: magnitudes (and/or colors, or fluxes) from
LSST Objects Catalog - ``float`` \* Observable errors: magnitude errors
(and/or color errors, or flux errors) from LSST Objects Catalog -
``float`` \* Right ascension [degrees] - ``float`` \* Declination
[degrees] - ``float`` \* Quality Flag - ``integer``, ``float``, or
``string`` \* Subset Flag - ``integer``, ``float``, or ``string``

.. code:: ipython3

    train_goldenspike = pz_server.get_product(9)

.. code:: ipython3

    train_goldenspike.display_metadata()

Display basic statistics

.. code:: ipython3

    train_goldenspike.data.describe()

Quick visualization of training set properties:

.. code:: ipython3

    train_goldenspike.plot(mag_name="mag_i_lsst")

.. container::
   :name: photo-z-validation-results

   `back to the top <#notebook-contents>`__

Photo-z Validation Results
--------------------------

Validation Results are the outputs of any photo-z algorithm applied on a
Validation Set. The format and number of files of this data product are
strongly dependent on the algorithm used to create it, so there are no
constraints on these two parameters. In the case of multiple files, for
instance, if the user includes the results of training procedures (e.g.,
neural nets weights, decision trees files, or any machine learning
by-product) or additional files (SED templates, filter transmission
curves, theoretical magnitudes grid, Bayesian priors, etc.), it will be
required to put all files together in a single compressed file (.zip or
.tar, or .tar.gz) before uploading it to the Photo-z Server.

List Validation Results available on PZ Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython3

    pz_server.display_products_list(filters={"product_type": "Validation Results"})

Display metadata of a given data product of Photo-z Validation Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython3

    pz_server.display_product_metadata("11_goldenspike_flexzboost")

Retrieve a given Photo-z Validation Results: download file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This product type is not necessarily (only) tabular data and can be a
list of files. The methods ``get_product`` shown above just return the
data to be used on memory and only supports single tabular files. To
retrieve Photo-z Validation Results, you must download the data to open
locally.

.. code:: ipython3

    # pz_server.download_product(11, save_in=".")

.. container::
   :name: photo-z-tables

   `back to the top <#notebook-contents>`__

Photo-z Tables
~~~~~~~~~~~~~~

The Photo-z Tables are the results of photo-z estimation on photometrics
samples. The data format is usually tabular, and might vary according to
the phto-z estimation method used.

The size limit for uploading files on the PZ Server is 200MB, therefore
it does not support large Photo-z Tables such as the photo-zs of the
LSST Objects catalog. The PZ Server can host small Photo-z Tables or, in
case of large datasets, a data product can be registered to contain only
the Photo-z Tables’ metadata. For these cases, the instructions to find
and access the data must be provided in the product’s description.

.. code:: ipython3

    # pz_server.download_product(<id number or internal name>)

--------------

Users feedback
~~~~~~~~~~~~~~

Is something important missing? `Click here to open an issue in the PZ
Server library repository on
GitHub <https://github.com/linea-it/pzserver/issues/new>`__.

