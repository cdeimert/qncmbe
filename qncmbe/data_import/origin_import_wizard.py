'''
Module for importing QNCMBE data into Origin. Call run_origin_import() to launch the gui.

Unlike origin_import_wizard_legacy, this does NOT run using the Python installed on Origin.
This uses the win32com.client interface to access Origin from the Python distribution installed on the computer.
This makes things much easier to install and gives greater flexibility.

Words of warning:
Many of the functions in win32com.client do not seem to work as expected. (E.g. Save() and Load())
The better approach seems to be to use Execute() and call LabTalk commands directly (https://www.originlab.com/doc/LabTalk/guide)

There's an alternative package OriginExt, which is much "cleaner" in the sense that everything can be done within Python.
However, OriginExt does not seem to handle errors very well.
When something goes wrong inside one of the functions (e.g. Load()), it tends to freeze rather than throw an exception.
This requires you to kill all the processes manually via task manager.
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
import win32com.client
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

		self.runtime_messages.setPlainText("Starting the import process...")
		self.runtime_messages.repaint()

		path = self.get_path()
		filename = self.get_file()

		if filename == "":
			self.runtime_messages.appendPlainText("Error: filename is missing. Check before running again.")
			return

		# Check path
		if not os.path.isdir(path):
			try:
				os.makedirs(full_path)
			except:
				self.runtime_messages.appendPlainText("Error: problem with the specified path. Check before running again.")
				return



		# Check timestep
		try:
			t_step = self.get_t_step()
		except:
			self.runtime_messages.appendPlainText("Error: invalid time step. Check before running again.")
			return

		generate_null_data = False
		if t_step == 0:
			generate_null_data = True
			self.runtime_messages.appendPlainText("Special case detected! (Time step = 0) Generating null data.")	
			self.runtime_messages.repaint()
		elif t_step <= 0.0:
			self.runtime_messages.appendPlainText("Error: time step must be positive. Change before running again")
			return

		# Check connections

		if not generate_null_data:
			insitudir = "\\\\insitu1.nexus.uwaterloo.ca\\Documents\\QNC MBE Data\\Production Data"

			try:
				if not os.path.exists(insitudir):
					raise Exception()
			except:
				self.runtime_messages.appendPlainText(f'Error: could not find/access "{insitudir}". Check before running again.')
				return

			svtdir = "\\\\insitu1.nexus.uwaterloo.ca\\QNC_MBE_Data\\ZW-XP1"

			try:
				if not os.path.exists(svtdir):
					raise Exception()
			except:
				self.runtime_messages.appendPlainText(f'Error: could not find/access "{svtdir}". Check before running again.')
				return


		# Check start and end times
		start_time = self.get_start_time()
		end_time = self.get_end_time()
		if (end_time < start_time):
			self.runtime_messages.appendPlainText("Error: end time is before start time. Check before running again.")
			self.runtime_messages.repaint()
			return
		if (end_time > dt.datetime.now()):
			self.runtime_messages.appendPlainText("Error: future times included. Check before running again.")
			return

		# Open Origin in background
		try:
			self.runtime_messages.appendPlainText("Loading Origin...")
			self.runtime_messages.repaint()
			origin = win32com.client.Dispatch("Origin.Application")
		except:
			self.runtime_messages.appendPlainText("Error: failed to load Origin.")
			del origin
			return

		
		# Open the template file
		try:
			self.runtime_messages.appendPlainText(f'Loading template "{self.default_template_file}"...')
			self.runtime_messages.repaint()
			if not origin.Execute(f'doc -o {self.default_template_file}'):
				raise Exception()
		except:
			self.runtime_messages.appendPlainText(f"Error: could not load template file. Check before running again.")
			del origin
			return

		# Save a copy of the template to the given filename
		full_filename = os.path.join(path, filename)
		try:
			self.runtime_messages.appendPlainText("Creating output file...")
			self.runtime_messages.repaint()
			if not origin.Execute(f'save {full_filename}'):
				raise Exception()
		except:
			self.runtime_messages.appendPlainText("Error: could not save to specified path/file. Check before running again.")
			del origin
			return	
		
		# Open Origin window
		origin.Visible = 1
		
		# Import data

		try:
			self.runtime_messages.appendPlainText('Collecting data... (this may take a while, and the window might say "Not Responding")')
			self.runtime_messages.repaint()
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

			self.runtime_messages.appendPlainText("Writing data to Origin...")
			self.runtime_messages.repaint()

			wkbk_names = {
				"Molly": "MollyData",
				"BET": "BETData",
				"SVT": "SVTData"
			}

			for loc in locs:

				#wks = origin.FindWorksheet(wksht_names[loc])

				origin.Execute(f'win -a {wkbk_names[loc]}') # Activate the workbook

				ncols = len(value_names[loc])
				origin.Execute(f'wks.ncols={ncols}') # Set the number of columns

				arr2d = np.stack([np.nan_to_num(data[name]) for name in value_names[loc]]).transpose()
				origin.PutWorksheet(wkbk_names[loc],arr2d.tolist(),0,0) # Set data in the worksheet

				for n in range(ncols):
					name = value_names[loc][n]
					units = value_names_database[name]['Units']

					origin.Execute(f'col({n+1})[L]$ = {name}') # Add name to each column
					origin.Execute(f'col({n+1})[U]$ = {units}') # Add units to each column

			origin.Execute(f'win -a ImportInfo')

			if generate_null_data:
				origin.PutWorksheet('ImportInfo',[[None],[None]],0,0)
			else:
				origin.PutWorksheet('ImportInfo',[[str(start_time)], [str(end_time)]], 0,0)
			
			origin.Execute(f'col(1)[L]$ = Start time')
			origin.Execute(f'col(2)[L]$ = End time')			

		except:
			self.runtime_messages.appendPlainText("Import failed.")
			del origin
			return

		try:
			self.runtime_messages.appendPlainText("Saving data...")
			self.runtime_messages.repaint()
			if not origin.Execute(f'save {full_filename}'):
				raise Exception()
		except:
			self.runtime_messages.appendPlainText("Error: could not save output file. Save manually if possible.")
			del origin
			return	

		t = tm.time() - t
		self.runtime_messages.appendPlainText("Import complete!\nRun time: {:.4f} (s)".format(t))

		del origin # Stop running Origin in the background (release control of the Origin file to the user)

def run_origin_import(template_file, out_path):

	argv = []
	app = QtWidgets.QApplication(argv)
	form = ImportFrame(template_file, out_path)
	form.show()
	app.exec_()
