'''
Simple script to launch the QNC-MBE Origin data import gui.

Requirements:
- Python must be installed (e.g., latest Anaconda distribution of Python 3.x)
- The Python module "qncmbe" must be installed (https://github.com/cdeimert/qncmbe). (Plus all its dependencies, but the installation process for qncmbe should take care of that.)
- Origin must be installed
- The template file Origin_digest_template.opj must be in the same folder as this file (or you have to adjust template_file below)
- You must have access to the entire \\insitu1.nexus.uwaterloo share (including the ZW-XP1 folder)

To run:
You can run this as you would any Python script. To enable "double click to run" behaviour, right click the file, select "Open with" and then point it to the location of your python.exe installation.
'''

from qncmbe.data_import.origin_import_wizard import run_origin_import
import os

this_dir = os.path.dirname(os.path.abspath(__file__)) # Get the full path of the folder containing this .py file

template_file = os.path.join(this_dir, "Origin_digest_template.opj")
default_out_path = this_dir

run_origin_import(template_file, default_out_path)