'''
Module for importing QNCMBE data into Origin. Call run_origin_import() to
launch the gui.

Unlike origin_import_wizard_legacy, this does NOT run using the Python
installed on Origin. This uses the win32com.client interface to access Origin
from the Python distribution installed on the computer.
This makes things much easier to install and gives greater flexibility.

Words of warning:
Many of the functions in win32com.client do not seem to work as expected.
(E.g. Save() and Load()) The better approach seems to be to use Execute() and
call LabTalk commands directly (https://www.originlab.com/doc/LabTalk/guide)

There's an alternative package OriginExt, which is much "cleaner" in the sense
that everything can be done within Python. However, OriginExt does not seem to
handle errors very well. When something goes wrong inside one of the functions
(e.g. Load()), it tends to freeze rather than throw an exception. This requires
you to kill all the processes manually via task manager.
'''

# Standard library imports (not included in setup.py)
import time as tm
import datetime as datetime
import os

# qncmbe imports
from .growths import GrowthDataCollector
from .data_names import index

# Non-standard library imports (included in setup.py)
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.Qt import QApplication
import win32com.client
import numpy as np


this_dir = os.path.dirname(os.path.abspath(__file__))

qt_creator_file = os.path.join(this_dir, "origin_import.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)


class ImportFrame(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(
        self, template_file=None, start_time=None, end_time=None,
        parent=None
    ):

        super(ImportFrame, self).__init__(parent)
        self.setupUi(self)

        self.import_button.clicked.connect(self.import_data)

        self.filepath_button.clicked.connect(self.select_filepath)

        self.template_button.clicked.connect(self.select_template_file)

        if end_time is None:
            self.set_default_end()
        else:
            self.end.setDateTime(end_time)

        if start_time is None:
            self.set_default_start()
        else:
            self.start.setDateTime(start_time)

        if template_file is not None:
            self.set_template_file(template_file)
            self.set_default_filepath()

    def get_start_time(self):
        return self.start.dateTime().toPyDateTime()

    def get_end_time(self):
        return self.end.dateTime().toPyDateTime()

    def get_filepath(self):
        return self.filepath.text()

    def set_filepath(self, filepath):
        self.filepath.setText(filepath)

    def get_template_file(self):
        return self.template_file.text()

    def set_template_file(self, template_file):
        self.template_file.setText(template_file)

    def get_empty_data(self):
        return self.empty_data_checkbox.isChecked()

    def set_default_start(self):
        end_time = self.get_end_time()
        start_time = end_time - datetime.timedelta(days=1)

        self.start.setDateTime(start_time)

    def set_default_end(self):
        end_time = (
            datetime.datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            - datetime.timedelta(days=1)
        )

        self.end.setDateTime(end_time)

    def set_default_filepath(self):

        self.set_filepath('')

    def get_folder(self):
        return os.path.dirname(self.get_filepath())

    def select_filepath(self):

        fpath = self.get_filepath()

        if fpath == '':

            template_file = self.get_template_file()

            if template_file != '':
                folder = os.path.dirname(template_file)

                start_time = self.get_start_time()

                start_str = start_time.strftime("%Y-%m-%d")

                fpath = os.path.join(
                    folder, f"Growth data {start_str}.opj"
                )
            else:
                fpath = QtCore.QDir.homePath()

        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Choose save file", fpath,
            "Origin file (*.opj)"
        )

        if fname != '':
            self.set_filepath(os.path.abspath(fname))

    def select_template_file(self):

        path = self.get_template_file()
        if path == '':
            path = QtCore.QDir.homePath()

        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose template file", path,
            "Origin file (*.opj)"
        )

        if fname != '':
            self.set_template_file(os.path.abspath(fname))

    def set_runtime_message(self, text):
        self.runtime_messages.setPlainText(text)
        self.runtime_messages.repaint()

    def add_runtime_message(self, text):
        self.runtime_messages.appendPlainText(text)
        self.runtime_messages.repaint()

    def make_save_path(self):

        path = self.get_folder()

        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError:
                self.add_runtime_message(
                    "Error: problem with the specified path. "
                    "Check before running again."
                )
                return False

        return True

    def check_dates(self):

        start_time = self.get_start_time()
        end_time = self.get_end_time()

        if (end_time < start_time):
            self.add_runtime_message(
                "Error: end time is before start time. "
            )
            return False

        if (end_time > datetime.datetime.now()):
            self.add_runtime_message(
                "Error: future times included."
            )
            return False

        return True

    def check_connections(self, collector):

        passed = True
        bad_paths = collector.find_bad_data_paths()

        for path in bad_paths:
            self.add_runtime_message(
                    f'Error: could not find/access data folder\n  "{path}"'
                )
            passed = False

        return passed

    def import_data(self):

        self.set_runtime_message("Starting the import process...")

        start_time = self.get_start_time()
        end_time = self.get_end_time()

        passed = self.check_dates()

        if not passed:
            return

        full_names_list = index.get_names_list('all')

        collector = GrowthDataCollector(
            start_time=start_time,
            end_time=end_time,
            names=full_names_list
        )

        empty_data = self.get_empty_data()

        if not empty_data:
            passed = self.check_connections(collector)

            if not passed:
                return

        filepath = self.get_filepath()
        passed = self.make_save_path()

        if not passed:
            return

        try:
            # Open Origin in background
            origin = None
            self.add_runtime_message("Loading Origin...")
            origin = win32com.client.Dispatch("Origin.Application")

            template_file = self.get_template_file()
            self.add_runtime_message(
                f'Loading template file...'
            )

            if (
                (not os.path.exists(template_file))
                or (not template_file.endswith('.opj'))
            ):

                self.add_runtime_message(
                    "Error: template file missing/invalid."
                    " Check before running again."
                )
                raise RuntimeError("Invalid template file.")

            if not origin.Execute(f'doc -o {template_file}'):
                self.add_runtime_message(
                    f"Error: could not load template file. "
                    "Check before running again."
                )
                raise RuntimeError("Error loading template file.")

            # Save a copy of the template to the given filename
            self.add_runtime_message("Creating output file...")
            if not origin.Execute(f'save {filepath}'):
                self.add_runtime_message(
                    "Error: could not save to specified path/file."
                    " Check before running again."
                )
                raise RuntimeError("Error saving to origin file.")

            # Open Origin window
            origin.Visible = 1

            # Import data

            if empty_data:
                self.add_runtime_message('Generating empty data...')
            else:
                self.add_runtime_message(
                    'Collecting data... (this may take a while, and the window'
                    ' might say "Not Responding")'
                )

            t = tm.time()

            locs = ["Molly", "BET", "SVT"]

            if empty_data:
                data = collector.initialize_data()
            else:
                data = collector.get_data()

            self.add_runtime_message("Writing data to Origin...")

            wkbk_names = {
                "Molly": "MollyData",
                "BET": "BETData",
                "SVT": "SVTData"
            }

            for loc in locs:

                loc_names = []

                for name in full_names_list:
                    if index[name].location == loc:
                        loc_names.append(name)

                # Activate the workbook
                origin.Execute(f'win -a {wkbk_names[loc]}')

                ncols = len(loc_names)*2

                # Set the number of columns
                origin.Execute(f'wks.ncols={ncols}')

                # Pad data with None in case column lengths are uneven
                max_len = 0
                for name in loc_names:

                    if len(data[name]) > max_len:
                        max_len = len(data[name])

                data_list = []

                for name in loc_names:

                    time = np.empty(max_len, dtype=object)
                    vals = np.empty(max_len, dtype=object)
                    time[:len(data[name])] = data[name].time
                    vals[:len(data[name])] = data[name].vals

                    data_list.append(time)
                    data_list.append(vals)

                arr2d = np.stack(data_list).transpose()

                # Set data in the worksheet
                origin.PutWorksheet(wkbk_names[loc], arr2d.tolist(), 0, 0)

                for n in range(ncols//2):
                    name = loc_names[n]
                    units = index[name].units

                    # Add time name and units
                    origin.Execute(f'col({2*n+1})[L]$ = Time')
                    origin.Execute(f'col({2*n+1})[U]$ = s')
                    origin.Execute(f'wks.col = {2*n+1}')
                    origin.Execute(f'wks.col.type = 4')

                    # Add data name and units
                    origin.Execute(f'col({2*n+2})[L]$ = {name}')
                    origin.Execute(f'col({2*n+2})[U]$ = {units}')
                    origin.Execute(f'wks.col = {2*n+2}')
                    origin.Execute(f'wks.col.type = 1')

            origin.Execute(f'win -a ImportInfo')

            if self.get_empty_data():
                origin.PutWorksheet('ImportInfo', [[None, None]], 0, 0)
            else:
                origin.PutWorksheet(
                    'ImportInfo', [[str(start_time), str(end_time)]], 0, 0
                )

            origin.Execute(f'col(1)[L]$ = Start time')
            origin.Execute(f'col(2)[L]$ = End time')

            self.add_runtime_message("Saving data...")
            if not origin.Execute(f'save {filepath}'):
                self.add_runtime_message(
                    "Error: could not save output file."
                    " Save manually if possible."
                )
                raise RuntimeError("Error saving data")

            t = tm.time() - t
            self.add_runtime_message(
                f"Import complete!\nRun time: {t:.4f} s"
            )
        except RuntimeError:
            self.add_runtime_message("Import failed!")
        finally:
            del origin


def run_origin_import(**kwargs):
    '''Starts the origin import gui

    Allowed kwargs:
        template_file   string Origin template file
        start_time      datetime object
        end_time        datetime object
    '''

    argv = []
    app = QApplication(argv)
    form = ImportFrame(**kwargs)
    form.show()
    app.exec_()
