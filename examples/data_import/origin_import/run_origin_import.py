'''
Simple script to launch the QNC-MBE Origin data import gui.

Requirements:
- Python must be installed (e.g., latest Anaconda distribution of Python 3.x)
- The Python module "qncmbe" must be installed
  (https://github.com/cdeimert/qncmbe). (Plus all its dependencies, but the
  installation process for qncmbe should take care of that. PyQt may need to
  be installed separately.)
- Origin must be installed
- The template file Origin_digest_template.opj must be in the same folder as
  this file (or you have to adjust template_file below)
- You must have access to the entire \\insitu1.nexus.uwaterloo share
  (including the ZW-XP1 folder)

To run:
You can run this as you would any Python script. To enable "double click to
run" behaviour, right click the file, select "Open with" and then point it to
the location of your python.exe installation.
'''

from qncmbe.data_import.origin_import import run_origin_import
import os

# Get the full path of the folder containing this .py file
this_dir = os.path.dirname(os.path.abspath(__file__))
default_template = os.path.join(this_dir, "Growth data template.opj")

test_mode = False

if test_mode:
    import datetime
    default_start = datetime.datetime(2019, 12, 23)
    default_end = datetime.datetime(2019, 12, 25)
else:
    default_start = None
    default_end = None

run_origin_import(
    template_file=default_template,
    start_time=default_start,
    end_time=default_end,
    test_mode=test_mode
)
