# PZ Server Library

![PyPI](https://img.shields.io/pypi/v/pzserver?label=PyPI)
![PyPI - Status](https://img.shields.io/pypi/status/pzserver)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/linea-it/pzserver/build-documentation.yml?label=docs)
![GitHub](https://img.shields.io/github/license/linea-it/pzserver)

A Python library to access data and services from the LSST [Photo-z Server](https://pz-server.linea.org.br/). 

The Photo-z (PZ) Server is an online service based on software developed and delivered as part of the in-kind contribution program BRA-LIN, from LIneA to the Legacy Survey of Space and Time (LSST) caried out by the [Rubin Observatory](https://rubinobservatory.org/). The PZ Server is an open source project. The source code is available on the GitHub repository [linea-it/pzserver](https://github.com/linea-it/pzserver). 
 
An overview of this and other contributions is available [here](https://linea-it.github.io/pz-lsst-inkind-doc/).  
The API documentation is available [here](https://linea-it.github.io/pzserver). 


This repo uses the [LINCC's Python Project Template](https://github.com/lincc-frameworks/python-project-template), described in the article: [A Python Project Template for Healthy Scientific Software](https://iopscience.iop.org/article/10.3847/2515-5172/ad4da1).

 
--- 

## Save your API token once

In your notebook or Python session, register the token generated on the PZ
Server website. The prompt hides your input, and the token is validated before
being saved:

```python
from pzserver import PzServer, login, logout

login()  # First use only: enter your token in the hidden prompt.
pz = PzServer()
```

In later sessions, including after kernel or Jupyter server restarts, use only:

```python
from pzserver import PzServer

pz = PzServer()
```

Tokens are stored **unencrypted** in `~/.pzserver/credentials`, outside your
notebooks. On POSIX systems, the credentials directory has permissions `0700`
and token files have permissions `0600`. Processes running as your user can
read them. On other systems, protect your home directory with the operating
system's access controls. Your home directory must be persistent for credentials
to survive a server restart; another environment needs its own login.

Credentials are stored separately for each API endpoint. For development, use
`login(host="pz-dev")` followed by `PzServer(host="pz-dev")`. Custom API URLs
are also supported. Only enter a token for an API you trust, using HTTPS for
remote servers.

Explicit credentials still work with `PzServer(token=token)` and take precedence
over saved credentials without saving or replacing them. If no saved token
exists, `PzServer()` raises an error directing you to `login()`; it never opens
an unexpected prompt. To replace an expired or revoked token, run `login()`
again. Tokens are not automatically renewed.

Use `logout()` (or `logout(host="pz-dev")`) to delete the local credential.
This does not revoke the token on the API or disconnect existing Python
instances. Revocation must be done on the PZ Server website.

## Partner JupyterHub authentication

Once the PzServer API administrator has enabled the `linea-dev` partner and
confirmed your active PzServer account has exactly the same username, you can use:

```python
pz = PzServer(host="pz-dev", hub="linea-dev")
```

This reads `JUPYTERHUB_API_TOKEN` from the notebook environment without saving
it. For `PzServer()` without an explicit token or partner, saved PzServer
credentials take precedence; otherwise the package recognizes the LIneA dev
Hub via `JUPYTERHUB_PUBLIC_HUB_URL` or `JUPYTERHUB_HOST`. If those variables
are unavailable, specify `hub="linea-dev"`. Explicit `token=...` always wins.

Partner credentials are sent only to the known production/development
PzServer API URLs, never automatically to a custom `host`. The API validates
the token with its configured partner endpoint and requires an active local
account with exactly the same username. It applies that account's permissions. Rubin/Nublado is not supported by this integration.
The backend must be deployed and configured before this mode will work.

## Training Set Maker HATS configuration

Select the release before setting the photometric options. The package fetches
that release's editable HATS configuration and submits the effective object with
the process. Flux output is the default:

```python
tsm = pz.training_set_maker("DP1 training set")
tsm.set_release(name="dp1")
tsm.set_config(
    {
        "flux_type": "cModel",
        "dereddening": "none",
        "convert_flux_to_mag": False,
    }
)
```

The flux type and dereddening value must be among the options exposed by the
selected release. Magnitude conversion is accepted only when the release has
enabled it. Advanced callers may provide a complete editable configuration as
the `hats_config` dictionary. Infrastructure paths and executor settings are
restored by the server and cannot be overridden by the client.

## Instructions for developers: 

### How to validate a PR 

Step-by-step procedure to test a new feature or bug fix from a particular branch not using a previously installed version (not the only way, just a suggestion): 

1. Clone the repository (first time only).
 
    ```
    git clone git@github.com:linea-it/pzserver.git
    # or git clone https://github.com/linea-it/pzserver.git
    ```
</p>

2. Enter the repository and checkout to the development branch.

    ```
    cd pzserver
    git fetch origin
    git checkout <development branch name>
    git pull
    ```
</p>
    
3. Create a new Conda environment free from `pzserver`  old version installation. Delete any existing one with the same same, if necessary. 

    ```
    conda remove --name pzserver --all
    conda create -n pzserver python=3.12
    conda activate pzserver
    conda install pip
    python -m pip install -e '.[dev]'
    python -m ipykernel install --user --name pzserver --display-name "Python (pzserver)"
    ```
</p>

4. Open Python prompt or notebook and import the library:

    ```
    from pzserver import PzServer
    token = "****"  # your toker 
    pz = PzServer(token)                                   
    ```  

--- 
