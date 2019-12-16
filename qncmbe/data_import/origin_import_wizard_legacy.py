'''
Module for importing QNCMBE data into Origin. Call run_origin_import() to launch the gui.

THIS MODULE IS NOW DEPRECATED due to the installation difficulties described below.

Note on installation:
This file uses the PyOrigin module, so it has to be run from the Python contained *within* Origin (Only included in recent versions of Origin!).
There are a few setup challenges, though. 

The Python distributed with Origin (at least up to v2017) does not have any features to install packages or update Python.
So, e.g., in Origin 2017, the Python version is 3.5.2. (You can find this by opening Origin and running Tools>Python Console...)

To use packages like numpy, you need to first install the exact same version of python (in this case 3.5.2) on your computer.
Then use pip install to install all the necessary packages.
It's important to use the *exact* same version of python, otherwise the packages may not work correctly in Origin. (E.g., even Python 3.5.6 might not work with 3.5.2!)

Then, you need to point Origin to the packages folder in this local python install (something like "...\Lib\site-packages" in the python install directory).
To do that, follow the steps here: http://blog.originlab.com/programming-python/get-access-to-external-python-packages-with-origins-embedded-python

Likely, you'll want to maintain two installations of Python -- one up-to-date for main use, and one mirroring Origin.
In that case, make sure Origin is pointing to the correct one.

Note: for later versions of Origin there seem to be some simplifications, but I was not able to get them to work on Origin v2017.
- https://www.originlab.com/doc/python/Run-Python-in-Origin
- https://www.originlab.com/fileExchange/details.aspx?fid=414
'''

# Standard library imports (not included in setup.py)
import time as tm
import datetime as dt
import os
import traceback

# qncmbe imports
from .origin_import_gui import Ui_MainWindow
from .data_import_utils import get_data, get_value_names_list
from .value_names import value_names_database, get_value_names_list

# Non-standard library imports (included in setup.py)
from PyQt5 import QtWidgets


try:
	import PyOrigin # Automatically installed with latest versions of Origin
except:
	raise Exception("Import PyOrigin failed. Need to run from within Origin, using the Python installed there.")

class ImportFrame(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self, parent=None):
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

		#self.start.setDateTime(dt.datetime(year=2016,month=7,day=21,hour=8))
		#self.end.setDateTime(dt.datetime(year=2016,month=7,day=21,hour=12))
		self.set_default_file()

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
		#start_time = end_time - dt.timedelta(hours=1)
		self.start.setDateTime(start_time)

	def set_default_end(self):
		end_time = dt.datetime.today().replace(second = 0, microsecond = 0)
		#end_time = dt.datetime(year = 2016, month = 7, day = 21, hour = 1)
		self.end.setDateTime(end_time)

	def set_default_path(self):
		self.path.setText(r"Z:\QNC MBE Data\Production Data\Growths\Origin template")

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

		full_filename = os.path.join(path, filename)
		if not PyOrigin.Save(full_filename):
			self.runtime_messages.setPlainText("Error: could not save to specified path/file. Check before running again.")
			return			

		try:
			t_step = self.get_t_step()
		except:
			self.runtime_messages.setPlainText("Error: invalid time step. Check before running again.")
			return

		if t_step <= 0.0:
			self.runtime_messages.setPlainText("Error: invalid time step. Check before running again.")
			return

		start_time = self.get_start_time()
		end_time = self.get_end_time()
		if (end_time < start_time):
			self.runtime_messages.setPlainText("Error: end time is before start time. Check before running again.")
			return
		if (end_time > dt.datetime.today()):
			self.runtime_messages.setPlainText("Error: future times included. Check before running again.")
			return

		try:
			t = tm.time()

			Molly_value_names = get_value_names_list("Molly")
			BET_value_names = get_value_names_list("BET")
			SVT_value_names = get_value_names_list("SVT")

			all_value_names = Molly_value_names + BET_value_names + SVT_value_names

			data = get_data(start_time, end_time, all_value_names, t_step)

			wks = PyOrigin.FindWorksheet("MollyData")

			for num, name in enumerate(Molly_value_names):
				wks.SetData([data[name]],0,num)
				wks.Columns(num).SetLongName(name)
				wks.Columns(num).SetUnits(value_names_database[name]['Units'])

			wks.Columns(0).SetComments("Data from " + str(start_time) + " to " + str(end_time))

			wks = PyOrigin.FindWorksheet("LabViewData")

			for num, name in enumerate(BET_value_names):
				wks.SetData([data[name]],0,num)
				wks.Columns(num).SetLongName(name)
				wks.Columns(num).SetUnits(value_names_database[name]['Units'])

			wks = PyOrigin.FindWorksheet("SVTData")

			for num, name in enumerate(SVT_value_names):
				wks.SetData([data[name]],0,num)
				wks.Columns(num).SetLongName(name)
				wks.Columns(num).SetUnits(value_names_database[name]['Units'])

			t = tm.time() - t
			self.runtime_messages.setPlainText("Import complete!\nRun time: {:.4f} (s)".format(t))
		except Exception as e:
		#	message = "There was an error during the import:\n"
		#	message += e.message
		#	self.runtime_messages.setPlainText(message)
			return

		PyOrigin.Save(full_filename)

def run_origin_import():

	argv = []
	app = QtWidgets.QApplication(argv)
	# app = QtGui.QApplication(sys.argv)
	form = ImportFrame()
	form.show()
	app.exec_()

if __name__ == "__main__":
	run_origin_import()
