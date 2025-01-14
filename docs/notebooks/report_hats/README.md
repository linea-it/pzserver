# Guide to Setting Up a Conda Environment on HPC and Integrating with Open OnDemand for report_hats

This guide describes the steps required to create a Conda environment on the HPC system, install dependencies using an `environment.yaml` file, and make the environment available as a Python kernel in Jupyter Notebook on the Open OnDemand platform for running the `report_hats` notebooks ([report_hats issue #140](https://github.com/linea-it/pzserver/issues/140)).

Author: [Luigi Lucas de Carvalho Silva](mailto:luigi.lcsilva@gmail.com)
Affiliation: [LIneA (Laboratório Interinstitucional de e-Astronomia)](https://www.linea.org.br/sobre-linea)

# Attention!

After following all the steps, you will probably want to run the Jupyter notebooks from `report_hats`. By default, all notebooks and scripts come with the parameter `run_the_pipeline == False`, meaning they will likely throw an error if you try to run them right away. 

This is intentional because it is very important that you <span style="color:red;">**KNOW WHAT YOU ARE DOING**</span> before running the notebooks. 

The paths must be correctly configured, the cluster resources must match your permissions, you must have enough quota to store the results (which can be very large), among other considerations.

The same applies if you are running .py and .sbatch files directly in the terminal. Before running them, you must adjust the paths in these files and ensure that the --output and --error directories in the .sbatch file exist.

---

## 1. Preparation

### 1.1. Install and Load Miniconda
Follow the steps below to set up Miniconda in your scratch:

```bash
# Navigate to your scratch directory
cd $SCRATCH

# Download the Miniconda installer
curl -L -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Make the installer executable
chmod +x Miniconda3-latest-Linux-x86_64.sh

# Run the installer specifying the path to your scratch
./Miniconda3-latest-Linux-x86_64.sh -p $SCRATCH/miniconda

# Activate Miniconda
source miniconda/bin/activate

# Deactivate the base environment (necessary to avoid conflicts)
conda deactivate
```

---

## 2. Create the Conda Environment Using the YAML File

### 2.1. Download the `environment.yaml` File
Ensure the `environment.yaml` file is available in the repository and copy it to your scratch:

```bash
# Copy the file to your scratch
cp /path/to/environment.yaml $SCRATCH/

# Navigate to the directory where the file is located
cd $SCRATCH
```

If you cloned the [pzserver repository](https://github.com/linea-it/pzserver) to your scratch, use:

```bash
# Copy the file to your scratch
cp $SCRATCH/pzserver/docs/notebooks/report_hats/environment.yaml $SCRATCH/

# Navigate to the directory where the file is located
cd $SCRATCH
```

### 2.2. Create and Activate the Environment

```bash
# Create the Conda environment specifying the scratch path
conda env create -p $SCRATCH/report_hats_env -f environment.yaml

# Activate the environment
conda activate $SCRATCH/report_hats_env/
```

---

## 3. Configure the Python Kernel in Jupyter Notebook

### 3.1. Install the Kernel in Jupyter
Ensure the environment is activated before running this command:

```bash
# Set the JUPYTER_PATH
export JUPYTER_PATH=$SCRATCH/.local

# Verify the JUPYTER_PATH value
echo $JUPYTER_PATH

# Install the kernel in Jupyter Notebook
python -m ipykernel install --prefix=$JUPYTER_PATH --name 'report_hats_env'
```

### 3.2. Verify Kernel Installation
The above command should generate output confirming that the kernel was successfully installed. Verify in Jupyter Notebook that the kernel button appears with the chosen name.

---

## 4. Open Jupyter Notebook on Open OnDemand

### 4.1. Start a JupyterLab Session
To start a JupyterLab session, follow the detailed instructions at:

[Open OnDemand Guide](https://docs.linea.org.br/processamento/uso/openondemand.html#jupyterlab)

### 4.2. Select the Kernel
In the JupyterLab interface, you will see the kernel created available for use. Select it to start working with the configured environment.

---

## 5. Final Considerations

- The `environment.yaml` file already includes all necessary dependencies, including `ipykernel`, so there is no need to install it manually.
- If you have any questions, consult the internal documentation or contact the [LIneA support team](https://docs.linea.org.br/suporte.html).

---
