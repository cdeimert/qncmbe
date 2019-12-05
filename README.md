# qncmbe
A collection of useful Python tools for the QNC-MBE lab at the University of Waterloo

- `dataexport` provides functions for gathering data from various computers in the MBE lab. Particularly aimed at collecting data after growths.

## Installation

### For basic users

You need to install Python first. If you don't have Python, the Anaconda (v3.x) distribution should come with almost all the packages you need (https://www.anaconda.com/distribution/).

If you do not have the full package with all its files and directories (e.g., from one of the authors), you need to download it from https://github.com/cdeimert/qncmbe.

Then, in a Command Prompt, navigate to the multipass folder, which contains `setup.py`. From there, run

```pip install .```

(If you installed Anaconda and did not add Python to the Windows PATH, you might need to do this from the *Anaconda Prompt* rather than the standard Command Prompt.)

### For developers

First, `git clone` the latest version from https://github.com/cdeimert/qncmbe

Then, from the main directory (the one containing `setup.py`) run 

```pip install -e .```

The `-e` is short for `--editable`. Essentially, it will install the package as a *link* to the current folder, rather than copying it into the python installation. So, when you `import` from a Python script, it will automatically import the latest version. 

So the `-e` flag is useful if you are planning to make changes to the module. However, it means that you have to maintain a local copy of the code.

## Authors

Chris Deimert (cdeimert@uwaterloo.ca)