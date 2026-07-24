Use these steps in the Rubin Observatory Science Platform Notebook Aspect, using the
`latest` image.

The recommended setup is to install `pzserver` in a small virtual environment
that reuses the Rubin-provided scientific stack, while ignoring packages
previously installed in `~/.local`.

There are two supported installation paths:

- from a JupyterLab terminal
- from a cell in a notebook that is already running with the default Rubin
  kernel

After either setup path, switch the notebook kernel to:

```text
Rubin latest + pzserver
```

## Option 1: Install from a JupyterLab terminal

Open a terminal in JupyterLab and run the following commands:

```bash
setup lsst_distrib

cd ~/notebooks

PYTHONNOUSERSITE=1 python -m venv --system-site-packages .venvs/pzserver-rubin-latest
source .venvs/pzserver-rubin-latest/bin/activate

export PYTHONNOUSERSITE=1

python -m pip install --no-deps --ignore-installed pzserver
```

Validate the installation:

```bash
python - <<'PY'
import site
import pzserver
from pzserver import PzServer, Catalog, SpeczCatalog, TrainingSet

print("ENABLE_USER_SITE:", site.ENABLE_USER_SITE)
print("pzserver:", pzserver.__file__)
print("version:", getattr(pzserver, "__version__", "unknown"))
print("OK")
PY
```

Expected result:

```text
ENABLE_USER_SITE: False
pzserver: /home/<username>/notebooks/.venvs/pzserver-rubin-latest/lib/python3.13/site-packages/pzserver/__init__.py
version: ...
OK
```

Register the virtual environment as a Jupyter kernel:

```bash
python -m ipykernel install --user \
  --name pzserver-rubin-latest \
  --display-name "Rubin latest + pzserver"
```

## Option 2: Install from a notebook cell

If you prefer not to use a terminal, open a notebook with the default Rubin
`latest` kernel and run this cell:

```python
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

venv_dir = Path.home() / "notebooks" / ".venvs" / "pzserver-rubin-latest"
kernel_name = "pzserver-rubin-latest"
display_name = "Rubin latest + pzserver"

env = os.environ.copy()
env["PYTHONNOUSERSITE"] = "1"

if venv_dir.exists():
    shutil.rmtree(venv_dir)

subprocess.check_call(
    [sys.executable, "-m", "venv", "--system-site-packages", str(venv_dir)],
    env=env,
)

python = venv_dir / "bin" / "python"

subprocess.check_call(
    [
        str(python),
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--ignore-installed",
        "pzserver",
    ],
    env=env,
)

subprocess.check_call(
    [
        str(python),
        "-m",
        "ipykernel",
        "install",
        "--user",
        "--name",
        kernel_name,
        "--display-name",
        display_name,
    ],
    env=env,
)

kernel_json = (
    Path.home()
    / ".local"
    / "share"
    / "jupyter"
    / "kernels"
    / kernel_name
    / "kernel.json"
)

with kernel_json.open() as f:
    spec = json.load(f)

spec.setdefault("env", {})
spec["env"]["PYTHONNOUSERSITE"] = "1"

with kernel_json.open("w") as f:
    json.dump(spec, f, indent=2)

subprocess.check_call(
    [
        str(python),
        "-c",
        (
            "import site, pzserver; "
            "print('ENABLE_USER_SITE:', site.ENABLE_USER_SITE); "
            "print('pzserver:', pzserver.__file__); "
            "print('version:', getattr(pzserver, '__version__', 'unknown'))"
        ),
    ],
    env=env,
)

print(f"Done. Now switch this notebook kernel to: {display_name}")
```

This cell creates the same isolated virtual environment, installs `pzserver`,
registers a Jupyter kernel, and configures that kernel to ignore the user site.
The current notebook will not automatically switch to the new kernel. After the
cell finishes, change the notebook kernel manually.

## Use the new kernel

Open the tutorial notebook, for example:

```text
pzserver/docs/notebooks/pzserver_tutorial.ipynb
```

Then select the kernel:

```text
Rubin latest + pzserver
```

The notebook will then use the isolated `pzserver` installation together with
the Rubin `latest` Science Pipelines environment.

If you need to use the environment again from a terminal, run:

```bash
cd ~/notebooks
source .venvs/pzserver-rubin-latest/bin/activate
export PYTHONNOUSERSITE=1
```
