# qncmbe
A collection of useful Python tools for the QNC-MBE lab at the University of Waterloo

- `dataexport` provides functions for gathering data from various computers in the QNC-MBE lab. Particularly aimed at collecting data after growths.
- `graded_alloys` provides functions for growing graded alloys with MBE. (Particularly in AlGaAs -- creating smoothly-graded alloys by varying the Al cell temperature as a function of time.)
- `normalization` provides functions for normalizing units. Can be useful when doing calculations mixing eV, kg, cm, nm, etc.
- `cell_usage` allows you to estimate effusion cell element consumption over time by examining the cell temperature history.
- `refl_fit` includes tools for fitting reflectance oscillations during MBE growth

## Installation

### For basic users

You need to install Python first. If you don't have Python, the Anaconda (v3.x) distribution should come with almost all the packages you need (https://www.anaconda.com/distribution/). Despite what the installer says, I would recommend that you DO add anaconda to your system PATH variable during installation.

To install this package, you need the full folder structure with all the python files. If you didnt' get this from one of the authors already, you should be able to download it from https://github.com/cdeimert/qncmbe.

Then, in a Command Prompt, navigate to the multipass folder, which contains `setup.py`. From there, run

```pip install .```

Or, alternatively, run something like
```pip install path\to\folder```
where `folder` is the folder containing `setup.py`.

(If you installed Anaconda and did not add Python to the Windows PATH, you might need to do this from the *Anaconda Prompt* rather than the standard Command Prompt.)

### Jupyter launcher

Some of the example files use Jupyter notebooks. If you installed Anaconda, then you should have Jupyter already.

Normally, you would launch Jupyter from the Anaconda Prompt with `jupyter notebook`. However, there's a tool called `start_jupyter_cm` (https://github.com/hyperspy/start_jupyter_cm) which makes it a little easier. 

To install, just run the following in a command prompt (or anaconda prompt):
`pip install start_jupyter_cm`
and then
`start_jupyter_cm`

After this, you can launch jupyter notebooks by navigating to the appropriate folder in the File Explorer, right-clicking, and pressing "Jupyter notebook here"

### For developers (people who plan to edit the code)

First, `git clone` the latest version from https://github.com/cdeimert/qncmbe to a directory of your choice.

Then, from the main directory (the one containing `setup.py`) run 

```pip install -e .```

The `-e` is short for `--editable`. Essentially, it will install the package as a *link* to the current folder, rather than copying it into the python installation. So, when you `import` from a Python script, it will automatically import the latest version. 

So the `-e` flag is useful if you are planning to make changes to the module. However, it means that you have to maintain a local copy of the code.

## To Do

- Add code for tracking element usage (`cellusage`)
- Add code for reflectance fitting (`reflfit`)
- Add code for analyzing Al dynamics measurements?

## Authors

Chris Deimert (cdeimert@uwaterloo.ca)