# Pz Server Library

![PyPI](https://img.shields.io/pypi/v/pzserver?label=PyPI)
![PyPI - Status](https://img.shields.io/pypi/status/pzserver)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/linea-it/pzserver/build-documentation.yml?label=docs)
![GitHub](https://img.shields.io/github/license/linea-it/pzserver)

A Python library to access data from the LSST [Photo-z Server](https://pz-server-dev.linea.org.br/). 

The Photo-z (PZ) Server is an online service based on software developed and delivered as part of the in-kind contribution program BRA-LIN, from LIneA to the Legacy Survey of Space and Time (LSST) caried out by the [Rubin Observatory](https://rubinobservatory.org/). The PZ Server is an open source project. The source code is available on the GitHub repository [linea-it/pzserver_app](https://github.com/linea-it/pzserver_app). 
 
An overview of this and other contributions is available [here](https://linea-it.github.io/pz-lsst-inkind-doc/).  
The API documentation is available [here](https://linea-it.github.io/pzserver). 


This repo uses the [LINCC's Python Project Template](https://github.com/lincc-frameworks/python-project-template), described in the article: [A Python Project Template for Healthy Scientific Software](https://iopscience.iop.org/article/10.3847/2515-5172/ad4da1).

 
--- 

## Instructions for developers: 

### How to validate a PR 

Step-by-step procedure to test a new feature or bug fix from a particular branch not using a previously installed version (not the only way, just a suggestion): 

1. Clone the repository and checkout to the development branch.
    ```
    git clone git@github.com:linea-it/pzserver.git
    cd pzserver 
    git checkout <development branch name>
    ```
    or just
   ```
   cd pzserver 
   git pull
   git checkout <development branch name>
   ```
   if you already have it.
    
3. Create a new Conda environment free from `pzserver`  old version installation
    ```
    conda create -n pzserver-dev
    conda activate pzserver-dev
    conda install pip
    pip install -e '.'
    ```

4. Open Python prompt or notebook and import the library:
   ```
   from pzserver import PzServer
   token = "****"  # your toker 
   host = "pz-dev" # or "localhost" if testing pipeline back-end locally
   pz = PzServer(token, host)                                   
   ```  

--- 
