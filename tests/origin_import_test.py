from qncmbe.data_import.origin_import_wizard_ext import run_origin_import
import os

this_dir = os.path.dirname(os.path.abspath(__file__))
template_file = os.path.join(this_dir, "Origin_digest_template.opj")
out_path = this_dir

run_origin_import(template_file, out_path)