# MIDAP
MIDAP is a flexible and user-friendly software for the automated analysis of live-cell microscopy images of bacteria growing in a monolayer in microfluidics chambers. Through its graphical user interface, a selection of state-of-the-art segmentation and tracking tools are provided, allowing the user to select the most suited ones for their particular data set. Thanks to its modular structure, additional segmentation and tracking tools can easily be integrated as they are becoming available. After running the automated image analysis, the user has the option to visually inspect and, if needed, manually correct segmentation and tracking.

## Standard Installation

The installation was tested on macOS Sequoia (15.1) and Ubuntu 22.04.

MIDAP requires Python 3.10. To create an environemnt with the right Python version, please use conda. Further instructions for the download of miniconda can be found [here](https://docs.anaconda.com/miniconda/install/).

### Installation with pip

Create a conda environment and install midap with pip within the conda environment:
```
conda create --name midap python=3.10
conda activate midap
pip install midap
```

### Clone of GitHub repository and installation with pip

In case you want to download the source code, you can also clone the repository and then install MIDAP using pip:

1. Clone of GitHub repository:
- Clone the repo, navigate to the directory containing the pipeline `cd midap`.
- Download the [latest release](https://github.com/Microbial-Systems-Ecology/midap/releases) and unpack the tar.gz-file. Then navigate to the unpacked directory using the command line `cd midap-VERSION` (and add your version number).

2. Create and activate the conda environment:

```
cd midap
conda create --name midap python=3.10
conda activate midap
pip install -e .
```

3. Once the conda environment is activated, you can run the module from anywhere via `midap`. If you run the pipeline for the first time, it will download all the required files (~3 GB). You can also manually (re)download the files using the command `midap_download`. The module accepts arguments and has the following signature:

```
usage: midap [-h] [--restart [RESTART]] [--headless] [--loglevel LOGLEVEL] [--cpu_only] [--create_config]

Runs the cell segmentation and tracking pipeline.

optional arguments:
  -h, --help           show this help message and exit
  --restart [RESTART]  Restart pipeline from log file. If a path is specified the checkpoint and settings file will be
                       restored from the path, otherwise the current working directory is searched.
  --headless           Run pipeline in headless mode, ALL parameters have to be set prior in a config file.
  --loglevel LOGLEVEL  Set logging level of script (0-7), defaults to 7 (max log)
  --cpu_only           Sets CUDA_VISIBLE_DEVICES to -1 which will cause most! applications to use CPU only.
  --create_config      If this flag is set, all other arguments will be ignored and a 'settings.ini' config file is
                       generated in the current working directory. This option is meant generate config file templates
                       for the '--headless' mode. Note that this will overwrite if a file already exists.
```

For an installation with GPU support, please refer to the documentation.   

## Documentation

The documentation can be found in the [wiki](https://github.com/Microbial-Systems-Ecology/midap/wiki).

## Issues

If you are having trouble with the package, please have a look at the [troubleshooting page](https://github.com/Microbial-Systems-Ecology/midap/wiki/Troubleshooting#creating-an-github-issue) 
and if necessary create an issue according to the instructions provided there.  
