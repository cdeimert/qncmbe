'''
Module for importing QNCMBE data into Origin. Call run_origin_import() to launch the gui.

This will run externally.
'''

# Standard library imports (not included in setup.py)
import time as tm
import datetime as dt
import os
import traceback

# qncmbe imports
from qncmbe.data_import.origin_import_gui import Ui_MainWindow
from qncmbe.data_import.data_import_utils import get_data, get_value_names_list
from qncmbe.data_import.value_names import value_names_database, get_value_names_list

# Non-standard library imports (included in setup.py)
from PyQt5 import QtWidgets
import OriginExt
import numpy as np

class ImportFrame(QtWidgets.QMainWindow,Ui_MainWindow):
	def __init__(self, template_file, out_path, parent=None):
		super(ImportFrame, self).__init__(parent)
		self.setupUi(self)

		self.import_button.clicked.connect(self.import_data)

		self.start_button.clicked.connect(self.set_default_start)
		self.end_button.clicked.connect(self.set_default_end)
		self.t_step_button.clicked.connect(self.set_default_t_step)
		self.path_button.clicked.connect(self.set_default_path)
		self.file_button.clicked.connect(self.set_default_file)

		self.set_default_end()
		self.set_default_start()

		self.set_default_file()

		self.default_out_path = out_path
		self.default_template_file = template_file

		self.set_default_runtime_messages()
		self.set_default_t_step()
		self.set_default_path()

	def get_start_time(self):
		return self.start.dateTime().toPyDateTime()

	def get_end_time(self):
		return self.end.dateTime().toPyDateTime()

	def get_t_step(self):
		return float(self.t_step.text())

	def get_path(self):
		return self.path.text()

	def get_file(self):
		return self.file.text()

	def set_default_start(self):
		end_time = self.get_end_time()
		start_time = end_time - dt.timedelta(days=1)
		self.start.setDateTime(start_time)

	def set_default_end(self):
		end_time = dt.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - dt.timedelta(days=1)
		self.end.setDateTime(end_time)

	def set_default_path(self):
		self.path.setText(self.default_out_path)

	def set_default_t_step(self):
		self.t_step.setText("2.0")

	def set_default_file(self):
		end_time = self.get_end_time()
		start_time = self.get_start_time()

		start_str = start_time.strftime("%Y-%m-%d_%H-%M-%S")
		end_str = end_time.strftime("%Y-%m-%d_%H-%M-%S")
		self.file.setText("Origin_data_" + start_str + "_to_" + end_str + ".opj")

	def set_default_runtime_messages(self):
		self.runtime_messages.setPlainText("(Messages will appear here.)")

	def import_data(self):

		self.runtime_messages.setPlainText("Importing...")
		
		self.runtime_messages.repaint()
		path = self.get_path()
		filename = self.get_file()
		if filename == "":
			self.runtime_messages.setPlainText("Error: filename is missing. Check before running again.")
			return

		if not os.path.isdir(path):
			try:
				os.makedirs(full_path)
			except:
				self.runtime_messages.setPlainText("Error: problem with the specified path. Check before running again.")
				return

		try:
			t_step = self.get_t_step()
		except:
			self.runtime_messages.setPlainText("Error: invalid time step. Check before running again.")
			return

		generate_null_data = False
		if t_step == 0:
			generate_null_data = True
		elif t_step <= 0.0:
			self.runtime_messages.setPlainText("Error: time step must be positive. Change before running again")
			return


		try:
			origin = OriginExt.Application()
		except:
			self.runtime_messages.setPlainText("Error: failed to load Origin.")
			return

		
		try:
			origin.Load(self.default_template_file)
		except:
			self.runtime_messages.setPlainText(f"Error: could not load template file {self.default_template_file}. Check before running again.")
			return

		full_filename = os.path.join(path, filename)
		
		if not origin.Save(full_filename):
			self.runtime_messages.setPlainText("Error: could not save to specified path/file. Check before running again.")
			return	
		
		origin.Visible = origin.MAINWND_SHOW
		
		start_time = self.get_start_time()
		end_time = self.get_end_time()
		if (end_time < start_time):
			self.runtime_messages.setPlainText("Error: end time is before start time. Check before running again.")
			return
		if (end_time > dt.datetime.now()):
			self.runtime_messages.setPlainText("Error: future times included. Check before running again.")
			return

		try:
			t = tm.time()

			locs = ["Molly", "BET", "SVT"]
			value_names = {loc: get_value_names_list(loc) for loc in locs}

			all_value_names = []
			for loc in locs:
				all_value_names = all_value_names + value_names[loc]

			if generate_null_data:
				data = {val: [] for val in all_value_names}
			else:
				data = get_data(start_time, end_time, all_value_names, t_step)

			wksht_names = {
				"Molly": "MollyData",
				"BET": "LabViewData",
				"SVT": "SVTData"
			}

			for loc in locs:

				wks = origin.FindWorksheet(wksht_names[loc])

				ncols = len(value_names[loc])

				if wks.GetColumns().GetCount() > ncols:
					self.runtime_messages.setPlainText("Error: too many columns in template file. Check before running again.")
					return

				wks.SetData([None], 0, ncols-1)

				for n, col in enumerate(wks.GetColumns()):
					name = value_names[loc][n]

					arr = data[name] if len(data[name])>0 else None
					wks.SetData([arr],0,n)

					col.SetLongName(name)
					col.SetUnits(value_names_database[name]['Units'])

			wks = origin.FindWorksheet("ImportInfo")

			if generate_null_data:
				wks.SetData([[None],[None],[None]])
			else:
				wks.SetData([[t_step],[str(start_time)], [str(end_time)]])
			
			cols = wks.GetColumns()
			
			col = next(cols)
			col.SetLongName('Time step')
			col.SetUnits('s')

			next(cols).SetLongName('Start time')
			next(cols).SetLongName('End time')

			t = tm.time() - t

			if generate_null_data:
				self.runtime_messages.setPlainText("Special case detected! (Time step = 0)\nGenerated null data (can be used as a template).\nRun again with a valid timestep to import real data.")	
			else:
				self.runtime_messages.setPlainText("Import complete!\nRun time: {:.4f} (s)".format(t))

		except:
			self.runtime_messages.setPlainText("Import failed.")
			return

		origin.Save(full_filename)

def run_origin_import(template_file, out_path):

	argv = []
	app = QtWidgets.QApplication(argv)
	form = ImportFrame(template_file, out_path)
	form.show()
	app.exec_()
