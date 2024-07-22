Photo-z Server
==============

Tutorial Notebook 0 - Introduction
----------------------------------

Contact author: `Julia Gschwend <mailto:julia@linea.org.br>`__

Last verified run: **2024-Jul-22**

The PZ Server
-------------

.. container::
   :name: introduction

Introduction
~~~~~~~~~~~~

The PZ Server is an online service available for the LSST Community to
host and share lightweight photo-z (PZ) -related data products. The
upload and download of data and metadata can be done at the website
`pz-server.linea.org.br <https://pz-server.linea.org.br/>`__ (during the
development phase, a test environment is available at
`pz-server-dev.linea.org.br <https://pz-server-dev.linea.org.br/>`__).
There, you will find two separate pages containing a list of data
products each: one for Rubin Observatory Data Management’s official data
products and the other for user-generated data products. **The
registered data products can also be accessed directly from Python code
using the PZ Server’s data access API, as demonstrated below.**

The PZ Server is developed and delivered as part of the in-kind
contribution program BRA-LIN, from LIneA to the Rubin Observatory’s LSST
project. The service is hosted in the Brazilian IDAC, not directly
connected to the `Rubin Science Platform
(RSP) <https://data.lsst.cloud/>`__. However, user authorization
requires the same credentials as RSP. For comprehensive documentation
about the PZ Server, please visit the `PZ Server’s documentation
page <https://linea-it.github.io/pz-lsst-inkind-doc/>`__. There, you
will also find an overview of all LIneA’s contributions related to the
PZ production. The internal documentation of the API functions is
available on the `API’s documentation
page <https://linea-it.github.io/pzserver>`__.

How to upload a data product on the PZ Server website
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To upload a data product, click on the button **NEW PRODUCT** on the top
left of the **User-generated Data Products** page and fill in the Upload
Form with relevant metadata. Alternatively, the user can upload files to
the PZ Server programmatically via the ``pzserver`` Python Library
(described below).

The photo-z-related products are organized into four categories (product
types):

-  **Spec-z Catalog:** Catalog of spectroscopic redshifts and positions
   (usually equatorial coordinates).
-  **Training Set:** Sample for training photo-z algorithms (tabular
   data). It usually contains magnitudes, errors, and true redshifts.
-  **Photo-z Validation Results:** The Results of a photo-z validation
   procedure (free format). They usually contain photo-z estimates
   (single estimates and/or PDFs) of a validation set, photo-z
   validation metrics, validation plots, etc.
-  **Photo-z Table**: This category is for the results of a photo-z
   estimation procedure. Ideally, the data should be in the same format
   as the photo-z tables delivered by the DM as part of the LSST data
   releases. If the data is larger than the file upload limit (200MB),
   the product entry will store only the metadata, and instructions on
   accessing the data should be provided in the description field.
   Storage space can be provided exceptionally for larger tables,
   depending on the science project justification (to be evaluated by
   IDAC’s management committee).

How to download a data product from the PZ Server website
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To download a data product available on the Photo-z Server, go to one of
the two pages by clicking on the card “Rubin Observatory PZ Data
Products” (for official products released by Rubin Data Management Team)
or “User-generated Data Products” (for products uploaded by the members
of LSST community). The **download** button is on the right side of each
data product (each row of the list). Also, there are buttons to
**share**, **remove**, and **edit** the metadata of a given data
product.

.. raw:: html

   <center>

.. raw:: html

   </center>

The PZ Server API (Python library ``pzserver``)
-----------------------------------------------

Installation
~~~~~~~~~~~~

**For regular users**

The PZ Server API is avalialble on **pip** as ``pzserver``. To install
the API and its dependencies, type, on the Terminal:

::

   $ pip install pzserver 

.. code:: ipython3

    ! pip install pzserver 

**For developers**

Alternatively, if you have cloned the repository with:

::

   $ git clone https://github.com/linea-it/pzserver.git  

To install the API and its dependencies, type:

::

   $ pip install .[dev]

--------------

OBS: You might need to restart the kernel on the notebook to incorporate
the new library.

Imports and Setup
~~~~~~~~~~~~~~~~~

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

    # pz_server = PzServer(token="<your token>", host="pz-dev") # "pz-dev" is the temporary host for test phase  

For convenience, the token can be saved into a file named as
``token.txt`` (which is already listed in the .gitignore file in this
repository).

.. code:: ipython3

    with open('token.txt', 'r') as file:
        token = file.read()
    pz_server = PzServer(token=token, host="pz-dev") # "pz-dev" is the temporary host for test phase  

How to get general info from PZ Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The object ``pz_server`` just created above can provide access to data
and metadata stored in the PZ Server. It also brings useful methods for
users to navigate through the available contents. The methods with the
preffix ``get_`` return the result of a query on the PZ Server database
as a Python dictionary, and are most useful to be used programatically
(see details on the `API documentation
page <https://linea-it.github.io/pzserver/html/index.html>`__).
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

Display all data products available (WARNING: this list can rapidly grow
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

How to upload a data product to via Python API (alternative method)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default method to upload a data product to the PZ Server is the
upload tool on PZ Server website, as shown above. Alternatively, data
products can be sent to the host service using the ``pzserver`` Python
library.

First, prepare a dictionary with the relevant information about your
data product:

.. code:: ipython3

    data_to_upload = {
        "name":"example upload via lib",
        "product_type": "specz_catalog",  # Product type 
        "release": None, # LSST release, use None if not LSST data 
        "main_file": "example.csv", # full path 
        "auxiliary_files": ["example.html", "example.ipynb"] # full path
    }

.. code:: ipython3

    upload = pz_server.upload(**data_to_upload)  

.. code:: ipython3

    upload.product_id

How to display the metadata of a data product
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The metadata of a given data product is the information provided by the
user on the upload form. This information is attached to the data
product contents and is available for consulting on the PZ Server page
or using this Python API (``pzserver``).

All data products stored on PZ Server are identified by a unique **id**
number or a unique name, a *string* called **internal_name**, which is
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To download any data product stored in the PZ Server, use the
``PzServer``\ ’s method ``download_product`` informing the product’s
**internal_name** and the path to where it will be saved (the default is
the current folder). This method downloads a compressed .zip file which
contais all the files uploaded by the user, including data, anciliary
files and description files. The time spent to download a data product
depends on the internet connection between the user and the host. Let’s
try it with a small data product.

.. code:: ipython3

    pz_server.download_product(14, save_in=".")

.. container::
   :name: how-to-share-data-products-with-other-rsp-users

   `back to the top <#notebook-contents>`__

How to share data products with other RSP users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

WARNING: The URL works only with the **complete internal name**, not
with just the **id** number.

.. container::
   :name: how-to-retrieve-contents-of-data-products-work-on-memory

   `back to the top <#notebook-contents>`__

How to retrieve contents of data products (work on memory)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

The tabular data is allocated in the attribute ``data``, which is a
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

In the prod-types you will see details about these specific classes. For
those who prefer working with ``astropy.Table`` or pure
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

Specific features for each product type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please take a look at the other tutorial notebooks with particular
examples of how to use the ``pzserver`` library to access and manipulate
data from the PZ Server.

--------------

Users feedback
~~~~~~~~~~~~~~

Is something important missing? `Click here to open an issue in the PZ
Server library repository on
GitHub <https://github.com/linea-it/pzserver/issues/new>`__.
