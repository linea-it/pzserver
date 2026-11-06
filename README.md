# PZ Server Library

![PyPI](https://img.shields.io/pypi/v/pzserver?label=PyPI)
![PyPI - Status](https://img.shields.io/pypi/status/pzserver)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/linea-it/pzserver/build-documentation.yml?label=docs)
![GitHub](https://img.shields.io/github/license/linea-it/pzserver)

A Python library to access data and services from the LSST [Photo-z Server](https://pzserver.linea.org.br/).

The Photo-z (PZ) Server is an online service based on software developed and delivered as part of the in-kind contribution program BRA-LIN, from LIneA to the Legacy Survey of Space and Time (LSST) caried out by the [Rubin Observatory](https://rubinobservatory.org/). The PZ Server is an open source project. The source code is available on the GitHub repository [linea-it/pzserver](https://github.com/linea-it/pzserver). 
 
An overview of this and other contributions is available [here](https://linea-it.github.io/pz-lsst-inkind-doc/).  
The API documentation is available [here](https://linea-it.github.io/pzserver). 


This repo uses the [LINCC's Python Project Template](https://github.com/lincc-frameworks/python-project-template), described in the article: [A Python Project Template for Healthy Scientific Software](https://iopscience.iop.org/article/10.3847/2515-5172/ad4da1).

 
--- 

## Sign in through your browser (Device Flow)

For an API with Device Flow enabled, specify the host once:

```python
from pzserver import PzServer

pz = PzServer(host="localhost", open_browser=False)
# If needed, open the displayed URL, enter the code and approve access.
# Construction waits for approval, then returns the authenticated client.
pz.get_product_types()
```

For local development, install this checkout into the notebook kernel with
`%pip install -e /home/singulani/projects/pzserver` and restart the kernel.
The `localhost` alias uses `http://localhost/api/`. If your local server uses a
port, pass the full API URL, e.g. `host="http://localhost:8080/api/"`.
A remote notebook's localhost is the notebook server, not your laptop.

On later runs, use the same constructor. It checks the saved credentials against
the API and only requests authorization when necessary. Near-expiry Device tokens
are renewed automatically. A rejected saved access token triggers renewal before
requesting another authorization. Explicit manual tokens and Hub selections retain
their existing authentication behavior.

For unattended scripts, use `PzServer(host="localhost", auto_login=False)` to fail
without opening a browser or waiting for approval. Network failures, server errors
and permission denials do not automatically start Device Flow.

The standalone `login_device` function remains available:
Calling `login_device(host="localhost")` again validates and renews the saved
credentials within the same authorization, without opening the browser or creating
another connection. If the refresh token expired or was revoked, it starts a new
browser authorization. Network/server errors do not trigger a new login.

To deliberately create another independent authorization, use
`PzServer(host="localhost", force=True)` (or the standalone
`login_device(host="localhost", force=True)`). This replaces the saved credentials
only after success and **does not revoke** the previous server authorization;
revoke unused connections from Connected applications in PzServer.

Access tokens last one hour; the package refreshes them before requests when fewer than 60
seconds remain. Each successful refresh restarts the server's 30-day renewal
window. If access is revoked after construction, instantiate a new client or run
`login_device` again. API writes are not automatically retried on 401.

Credentials are stored **unencrypted** in `~/.pzserver/credentials`, separately
for each API, in private files (`0600`) inside a private directory (`0700`) on
POSIX. The home directory must persist across notebook restarts. A file lock
serializes refresh across instances/processes; refresh rotation is saved with
an atomic replacement. Anyone running as your OS user can read these files.

Use `open_browser=False` on a remote notebook and open the printed URL yourself.
Only the verification URL and user code are displayed. HTTPS is required except
for HTTP on loopback during local testing. OAuth requests do not follow redirects.
No JupyterHub token is used by this flow.

Saved Device credentials take precedence over saved manual tokens and automatic
Hub detection. An explicit `token=` or `hub=` still selects the existing flow.
`logout(host=...)` forgets both kinds of saved credentials locally; it does not
revoke them on the server. Existing Device instances cannot make new requests
after their saved credentials are removed. Server-side revocation is available
in Connected applications on the PzServer website.

### Pending authorization and retry limits

A code is valid for **15 minutes** by default. Its verification link identifies
that specific request: open the full URL printed by Python. The server tells the
package how many incorrect code entries are allowed (the default is **3**). Once
that limit is reached, the request is blocked even if you switch browsers. A
correct code entered before the limit proceeds to the approval screen. These
errors are unrelated to your account password or the package's background polling.

If you interrupt Python, the pending request is saved in a private file next to
the credentials. Running the constructor/login again resumes the same code without
extending its expiry. Only one local login process per API may wait for approval;
interrupt the old execution before restarting. To explicitly replace the pending
request, call:

```python
from pzserver import PzServer
pz = PzServer(host="localhost", force=True)
```

The package first cancels the pending request on the server, then requests another.
A cancellation failure does not issue a new code. Expired, denied or blocked
requests require a new authorization. Previously issued access tokens are not
revoked by this restart. Update the backend together with the package for pending
request cancellation support.

While waiting, the package checks for approval at the interval reported by the
server (normally **5 seconds**). `authorization_pending` simply means “not yet”.
An early poll receives `slow_down`, increasing the wait by **5 seconds** (5 → 10 →
15...). The increased interval is retained after interruption. Polling stops on
approval, denial, blocking, cancellation or expiry; it does not count as entering
an incorrect code. Server rate limits return HTTP 429; wait before retrying.

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
over saved credentials without saving or replacing them. If no saved credential or usable Hub credential
exists, `PzServer()` starts Device Flow unless `auto_login=False`. A saved manual
token rejected with HTTP 401 can also transition to Device Flow. To replace a
manual token directly, run `login()` again; manual tokens are not automatically renewed.

Use `logout()` (or `logout(host="pz-dev")`) to delete the local credential.
For manual tokens, this does not revoke the token on the API or disconnect existing Python
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
    from pzserver import PzServer, login

    login()  # First use only: enter the API token in the hidden prompt.
    pz = PzServer()
    ```  

--- 
