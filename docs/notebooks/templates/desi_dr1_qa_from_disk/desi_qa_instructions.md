# Setup for desi_qa_env on LIneA JupyterHub K8S

## Step 1: Create the conda environment from the YAML file
```bash
conda env create -p $HOME/.conda/envs/desi_qa_env -f /path/to/desi_qa_env.yaml
```

Obs.: replace `/path/to/desi_qa_env.yaml` with the actual path to your YAML file.

## Step 2: Activate the environment
```bash
conda activate $HOME/.conda/envs/desi_qa_env
```

## Step 3: Register the environment as a Jupyter kernel
```bash
python -m ipykernel install --user --name=desi_qa_env
```

## Step 4: Select and run the kernel in a notebook
Open a notebook, go to the top-right corner menu Kernel → Change kernel, and select desi_qa_env.

⚠️ Important: This notebook was designed to run on the LIneA JupyterHub K8S platform using the "large" resource profile (16GB RAM, 8 threads).

If you select a smaller configuration (e.g., "medium" or "small"), you must adjust the Dask Client() resource settings accordingly in the notebook to avoid memory or thread issues.