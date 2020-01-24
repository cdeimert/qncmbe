# qncmbe
A collection of useful Python tools for the QNC-MBE lab at the University of Waterloo.

- `cell_usage_tracking` allows you to estimate effusion cell element consumption over time by examining the cell temperature history.
- `data_import` provides functions for gathering data from various computers in the QNC-MBE lab. Particularly aimed at collecting data after growths.
- `graded_alloys` provides functions for growing graded alloys with MBE. (Particularly in AlGaAs -- creating smoothly-graded alloys by varying the Al cell temperature as a function of time.)
- `plotting` includes some useful plotting functions. It also includes style files to make `matplotlib` look a little nicer, and to help with following journal guidelines.
- `refl_fit` includes tools fitting reflectance oscillations during MBE growth
- `refl_sim` includes a simple transfer matrix simulator for calculating reflectance oscillations vs time.

Check out the example scripts!

## Installation

Note that many of these scripts will only run properly when given access to the QNC-MBE shared drive, which is restricted to QNC-MBE group members.

### Installing Python

You need to install Python first. If you don't have Python, the Anaconda (v3.x) distribution should come with almost all the packages you need (https://www.anaconda.com/distribution/).

It is assumed below that Anaconda was used. Otherwise, the instructions should be similar, though.

### Installation

Open Anaconda Navigator.

QNC-MBE group members with an appropriately setup Z: drive should be able to run

```pip install Z:\Lab_code_repository\Python_modules\qncmbe```

Non-QNC-MBE members must obtain the source code (e.g., from https://github.com/cdeimert/qncmbe) and save it somewhere. Navigate to the folder containing `setup.py` and run

```pip install .```

Note: to use `qncmbe.data_import.origin_import_wizard`, you may need to install PyQt separately, as pip is not able to automatically install it.
In Anaconda, PyQt was likely already installed. 
If not, you may have to run `conda install pyqt`.

### Jupyter launcher

Some of the example files use Jupyter notebooks. If you installed Anaconda, then you should have Jupyter already.

Normally, you would launch Jupyter from the Anaconda Prompt with `jupyter notebook`. However, there's a tool called `start_jupyter_cm` (https://github.com/hyperspy/start_jupyter_cm) which makes it a little easier. 

To install, just run the following in a command prompt (or anaconda prompt):
`pip install start_jupyter_cm`
and then
`start_jupyter_cm`

After this, you can launch jupyter notebooks by navigating to the appropriate folder in the File Explorer, right-clicking, and pressing "Jupyter notebook here"

### For developers

`git clone` the latest version from https://github.com/cdeimert/qncmbe to a directory of your choice.

Then, from the main directory (the one containing `setup.py`) run 

```pip install -e .```

The `-e` is short for `--editable`. Essentially, it will install the package as a *link* to the current folder, rather than copying it into the python installation. So, when you `import` from a Python script, it will automatically import the latest version. 

So the `-e` flag is useful if you are planning to make changes to the module. However, it means that you have to maintain a local copy of the code.

## Authors

Chris Deimert - cdeimert@uwaterloo.ca
