'''
Module for importing QNCMBE data into Origin. Call run_origin_import() to
launch the gui.

Unlike origin_import_wizard_legacy, this does NOT run using the Python
installed on Origin. This uses the win32com.client interface to access Origin
from the Python distribution installed on the computer.
This makes things much easier to install and gives greater flexibility.
'''

# Standard library imports (not included in setup.py)
import time as tm
import datetime as datetime
import os
import logging
from textwrap import dedent
import re
from pathlib import Path

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

# TODO: switch back to pyuic5 for loading the .ui
# Could add a switch to load directly from the .ui file for
# development mode

logging.addLevelName(logging.ERROR, 'Error')
logging.addLevelName(logging.WARNING, 'Warning')
logging.addLevelName(logging.INFO, 'Info')


#
# TODO: for better organization, split OriginImportGui into 3 classes
#   - OriginInterface to deal with reading/writing from Origin. This should be
#     a class with __enter__ and __exit__ functions so it can use the
#     "with ... as:" syntax.
#   - OriginImport, to import data from a selected time range into Origin
#   - OriginImportGui, to deal with the Qt interface
#
#   Also, create unit tests...
#


class OriginError(Exception):
    pass


class OriginInterface():
    '''Functions for reading/writing to Origin. Uses the win32com.client
    interface with Origin.

    Developer notes:
    Most of these commands are implemented by using Execute() to call LabTalk
    commands directly (https://www.originlab.com/doc/LabTalk/guide).

    This seems to be the most reliable way to interface with Origin. The
    higher level functions from win32com (e.g., Save or Load) do not always
    work as expected.

    The alternative package OriginExt seems cleaner, but I found that it has
    poor error handling. If something goes wrong, it tends to freeze rather
    than throw an exception, requiring the user to manually kill Origin from
    the task manager. (And it may not even be obvious to the user that Origin
    is running in the first place.)

    NOTE: Apparently there is a new package called originpro which is supposed
    to be better. I haven't tried it.

    NOTE: even though the Execute(LabTalk command) approach is more reliable
    than the other approaches, it still freezes sometimes. Caution is required.

    Also note that input sanitation is important when pasting strings into
    LabTalk commands'''

    def __enter__(self):
        self.app = win32com.client.Dispatch("Origin.Application")

        return self

    def execute(self, command):
        '''Execute LabTalk command'''
        return self.app.Execute(command)

    @staticmethod
    def sanitize_string(string):

        # https://www.originlab.com/doc/LabTalk/ref/LT-Keywords
        repl_list = [
            ('\"', '%(quote)'),
            ('\t', '%(tab)'),
            ('\r\n', '%(crlf)'),
            ('\r', '%(cr)'),
            ('\n', '%(lf)')
        ]

        for s1, s2 in repl_list:
            string = string.replace(s1, s2)

        return string

    @staticmethod
    def sanitize_path(filepath):

        p = Path(filepath).resolve()

        return OriginInterface.sanitize_string(str(p))

    @staticmethod
    def validate_shortname(name):

        if not re.match('^[a-zA-Z0-9]+$', name):
            raise ValueError(
                "Shortname cannot include whitespace or special chars."
            )

        return True

    def load(self, filename):
        '''Load Origin file from specified path. Return True if successful.'''
        fn = self.sanitize_path(filename)
        return self.execute(f'doc -o "{fn}"')

    def save(self, filename):
        '''Save Origin file to specified path. Return True if successful.'''
        fn = self.sanitize_path(filename)
        return self.execute(f'save {fn}')

    def activate_workbook(self, name):
        '''Activate workbook by name. Create it if it doesn't exist.
        '''

        self.validate_shortname(name)

        if self.execute(f'win -a "{name}"'):
            return True
        else:
            return self.execute(
                f'newbook name:="{name}" sheet:=0 option:=lsname'
            )

    def activate_worksheet(self, name):
        '''Activate worksheet by name (within the current active workbook).
        Create it if it doesn't exist.'''

        self.validate_shortname(name)
        if self.execute(f'page.active$ = "{name}"'):
            return True
        else:
            return self.execute(f'newsheet name:="{name}" cols:=0')

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.app.Exit()
        except TypeError:
            del self.app


class QPlainTextEditHandler(logging.Handler):
    '''Handler to add log messages (info, warnings, errors, etc) to
    a Qt gui textbox.'''
    def __init__(self, plain_text_edit_widget):
        super().__init__()
        self.widget = plain_text_edit_widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.repaint()


class OriginImportGui(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(
        self, template_file=None, start_time=None, end_time=None,
        parent=None, test_mode=False
    ):

        super(OriginImportGui, self).__init__(parent)
        self.setupUi(self)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.start_gui_logger()

        self.import_button.clicked.connect(self.import_data)

        self.save_file_button.clicked.connect(self.select_save_file)

        self.template_file_button.clicked.connect(self.select_template_file)

        if end_time is None:
            self.set_default_end_time()
        else:
            self.end_time_edit.setDateTime(end_time)

        if start_time is None:
            self.set_default_start_time()
        else:
            self.start_time_edit.setDateTime(start_time)

        if template_file is not None:
            if os.path.exists(template_file):
                self.set_template_file(template_file)
            else:
                self.logger.warning(
                    f'Could not find template file "{template_file}".'
                    ' Please select template file manually.'
                )

        self.start_date = None
        self.end_date = None
        self.template_file = None
        self.save_file = None
        self.log_file = None
        self.do_empty_data = None

        self.test_mode = test_mode

    def start_gui_logger(self):

        # Handler for gui runtime message box
        self.gui_log_handler = QPlainTextEditHandler(self.runtime_messages)

        self.gui_log_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )

        self.gui_log_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(self.gui_log_handler)

    def read_start_time(self):
        self.start_time = self.start_time_edit.dateTime().toPyDateTime()

    def read_end_time(self):
        self.end_time = self.end_time_edit.dateTime().toPyDateTime()

    def read_save_file(self):
        self.save_file = self.save_file_display.text()

    def set_save_file(self, save_file):
        self.save_file = save_file
        self.save_file_display.setText(save_file)

    def read_template_file(self):
        self.template_file = self.template_file_display.text()

    def set_template_file(self, template_file):
        self.template_file = template_file
        self.template_file_display.setText(template_file)

    def read_empty_data_checkbox(self):
        self.do_empty_data = self.empty_data_checkbox.isChecked()

    def set_default_start_time(self):
        self.read_end_time()
        self.start_time = self.end_time - datetime.timedelta(days=1)

        self.start_time_edit.setDateTime(self.start_time)

    def set_default_end_time(self):
        self.end_time = (
            datetime.datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            - datetime.timedelta(days=1)
        )

        self.end_time_edit.setDateTime(self.end_time)

    def get_save_folder(self):
        return os.path.dirname(self.save_file)

    def select_save_file(self):

        self.read_save_file()

        if self.save_file == '':

            self.read_template_file()
            self.read_start_time()

            if self.template_file != '':
                folder = os.path.dirname(self.template_file)

                start_str = self.start_time.strftime("%Y-%m-%d")

                self.save_file = os.path.join(
                    folder, f"Growth data {start_str}.opj"
                )
            else:
                self.save_file = QtCore.QDir.homePath()

        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Choose save file", self.save_file,
            "Origin file (*.opj)"
        )

        if fname != '':
            self.set_save_file(os.path.abspath(fname))

    def select_template_file(self):

        self.read_template_file()

        if self.template_file == '':
            self.template_file = QtCore.QDir.homePath()

        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose template file", self.template_file,
            "Origin file (*.opj)"
        )

        if fname != '':
            self.set_template_file(os.path.abspath(fname))

    def clear_runtime_message(self):
        self.runtime_messages.setPlainText('')

    def set_runtime_message(self, text):
        self.clear_runtime_message()
        self.logger.info(text)

    def add_runtime_message(self, text, newline=True):
        self.logger.info(text)

    def make_save_path(self):

        path = self.get_save_folder()

        if path == '':
            self.logger.error("Missing save path.")
            return False

        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError:
                self.logger.error(
                    "Could not create the specified save path."
                )
                return False

        return True

    def check_dates(self):

        if (self.end_time < self.start_time):
            self.logger.error(
                "End time is before start time. "
            )
            return False

        if (self.end_time > datetime.datetime.now()):
            self.logger.error(
                "Future times included."
            )
            return False

        if ((self.end_time - self.start_time) > datetime.timedelta(days=14)):
            self.clear_runtime_message()
            self.logger.error(
                "Time range too wide! Must be less than 14 days."
            )
            return False

        return True

    def check_connections(self, collector):

        passed = True
        bad_paths = collector.find_bad_data_paths()

        for path in bad_paths:
            self.logger.error(
                    f'Could not find/access data folder "{path}"'
                )
            passed = False

        return passed

    def load_origin(self):
        self.origin = None
        self.add_runtime_message("Loading Origin...")
        self.origin = win32com.client.Dispatch("Origin.Application")

    def load_template_file(self):
        self.add_runtime_message('Loading template file...')

        if (
            (not os.path.exists(self.template_file))
            or (not self.template_file.endswith('.opj'))
        ):
            self.logger.error("Template file missing/invalid.")
            raise RuntimeError("Invalid template file.")

        if not self.origin.Execute(f'doc -o {self.template_file}'):
            self.logger.error("Could not load template file.")
            raise RuntimeError("Error loading template file.")

    def save_template_copy(self):
        # Save a copy of the template to the given filename
        self.add_runtime_message("Creating output file...")
        if not self.origin.Execute(f'save {self.save_file}'):
            self.logger.error("Could not save to specified path/file.")
            raise RuntimeError("Error saving to origin file.")

    def generate_log_header(self):
        header = dedent(f'''\
            ##### Data import info #####

            QNC-MBE growth data imported to Origin file:
            "{self.save_file}"
            using template file:
            "{self.template_file}"

        ''')

        if self.do_empty_data:
            header += '(Generated empty data.)\n\n'
        else:
            header += dedent(f'''\
                Data range from
                {self.start_time} (defined as t=0)
                to
                {self.end_time}

            ''')

        header += dedent('''\
            This data was imported using the qncmbe Python package
            (https://github.com/cdeimert/qncmbe)


            ##### Runtime log #####

        ''')
        return dedent(header)

    def initialize_log_file(self):

        if not self.make_save_path():
            return False

        prefix = os.path.splitext(self.save_file)[0]
        postfix = '-import-log.txt'

        n = 0
        while os.path.exists(prefix + postfix):
            n += 1
            postfix = f'-import-log-{n}.txt'
            if n > 100:
                self.logger.error(
                    'Too many existing import log files for output'
                    f' file "{self.save_file}"'
                )
                return None

        self.log_file = os.path.abspath(prefix + postfix)
        header = self.generate_log_header()
        try:
            with open(self.log_file, 'w') as lf:
                lf.write(header)
        except (IOError, OSError):
            self.logger.error(
                "Could not generate log file."
            )
            return False

        return True

    def clear_file_logger(self):
        if hasattr(self, 'log_file_handler'):
            root = logging.getLogger()
            if self.log_file_handler in root.handlers:
                root.removeHandler(self.log_file_handler)

    def start_file_logger(self):
        '''Assumes start_time, end_time, and save_file members are updated.'''

        self.clear_file_logger()
        if not self.initialize_log_file():
            return False

        self.log_file_handler = logging.FileHandler(self.log_file)
        self.log_file_handler.setLevel(logging.INFO)

        self.log_file_handler.setFormatter(
            logging.Formatter(
                    '%(levelname)s (%(name)s %(asctime)s):\n  %(message)s'
            )
        )

        logging.getLogger().addHandler(self.log_file_handler)

        return True

    def import_data(self):

        self.clear_file_logger()

        self.set_runtime_message("Starting the import process...")

        # Update member variables based on current state of the gui
        # Will not update them again until the import is done, so user changes
        # mid-import will be ignored until the next import
        self.read_start_time()
        self.read_end_time()
        self.read_save_file()
        self.read_template_file()
        self.read_empty_data_checkbox()

        self.add_runtime_message("Setting up log file...")
        if not self.start_file_logger():
            return

        self.add_runtime_message(f'Created log file "{self.log_file}"')

        t = tm.time()

        if self.do_empty_data:
            # If generating empty data, set fake time range to make sure
            # datetime checks are passed.
            delta = datetime.timedelta(hours=1)
            self.end_time = datetime.datetime.now() - delta
            self.start_time = self.end_time - delta

        if not self.check_dates():
            self.clear_file_logger()
            return

        full_names_list = index.get_names_list('all')

        collector = GrowthDataCollector(
            start_time=self.start_time,
            end_time=self.end_time,
            names=full_names_list
        )

        if self.test_mode:
            collector.set_test_mode()

        if not self.do_empty_data:
            if not self.check_connections(collector):
                self.clear_file_logger()
                return

        if not self.make_save_path():
            self.clear_file_logger()
            return

        try:
            self.load_origin()

            self.load_template_file()

            self.save_template_copy()

            # Import data

            if self.do_empty_data:
                self.add_runtime_message('Generating empty data...')
            else:
                self.add_runtime_message(
                    'Collecting data... (this may take a while, and the window'
                    ' might say "Not Responding")'
                )

            locs = ["Molly", "BET", "SVT"]

            if self.do_empty_data:
                data = collector.initialize_data()

            wkbk_names = {
                "Molly": "MollyData",
                "BET": "BETData",
                "SVT": "SVTData"
            }

            for loc in locs:

                names = index.get_names_list(loc)

                if not self.do_empty_data:
                    tcol = tm.time()
                    self.add_runtime_message(f'Collecting {loc} data...')
                    collector.set_names(names)
                    collector.get_data()
                    data = collector.data
                    dt = tm.time() - tcol
                    self.add_runtime_message(
                        f"Done collecting {loc} data. ({dt:.4f} s)"
                    )

                twrite = tm.time()
                self.add_runtime_message(f"Writing {loc} data to Origin...")

                # Activate the workbook
                if not self.origin.Execute(f'win -a {wkbk_names[loc]}'):
                    self.origin.Execute(
                        f'newbook name:={wkbk_names[loc]} sheet:=0'
                        ' option:=lsname'
                    )

                sublocs = []
                subloc_names = {}

                for name in names:
                    subloc = index[name].sublocation
                    if subloc not in sublocs:
                        sublocs.append(subloc)
                        subloc_names[subloc] = []

                    subloc_names[subloc].append(name)

                for subloc in sublocs:

                    ncols = len(subloc_names[subloc])*2

                    # If first time, create the worksheet
                    if self.origin.Execute(f'page.active$ = {subloc}'):
                        self.origin.Execute(f'wks.ncols={ncols}')
                    else:
                        self.origin.Execute(
                            f'newsheet name:={subloc} cols:={ncols}'
                        )

                    self.origin.Execute('wks.nrows=0')

                    # Note: it might seem cleaner to delete all the columns
                    # first and add them one-by-one, but this ruins any plots
                    # included in the template

                    n = 0

                    for name in subloc_names[subloc]:

                        # Put data on the workshe
                        time = data[name].time
                        vals = data[name].vals
                        units = data[name].units

                        arr2d = np.vstack((time, vals))

                        self.origin.PutWorksheet(
                            wkbk_names[loc], arr2d.T.tolist(), 0, n
                        )

                        # Add time name and units
                        self.origin.Execute(f'col({n+1})[L]$ = Time')
                        self.origin.Execute(f'col({n+1})[U]$ = s')

                        # Set as X-type column for plotting
                        self.origin.Execute(f'wks.col = {n+1}')
                        self.origin.Execute('wks.col.type = 4')

                        # Add data name and units
                        self.origin.Execute(f'col({n+2})[L]$ = {name}')
                        self.origin.Execute(f'col({n+2})[U]$ = {units}')

                        # Set as Y-type column for plotting
                        self.origin.Execute(f'wks.col = {n+2}')
                        self.origin.Execute('wks.col.type = 1')

                        n += 2

                    # Display long name and units rows only
                    self.origin.Execute('wks.labels(LU)')

                    # Resize columns to fit
                    self.origin.Execute('wautosize')

                self.origin.Execute('page.active = 1')

                dt = tm.time() - twrite
                self.add_runtime_message(
                    f"Done writing {loc} data to Origin. ({dt:.4f} s)"
                )

            # Write start and end dates to ImportInfo table
            if not self.origin.Execute('win -a ImportInfo'):
                self.origin.Execute(
                    'newbook name:=ImportInfo sheet:=0 option:=lsname'
                )

            if self.origin.Execute('page.active$ = ImportInfo'):
                self.origin.Execute('wks.ncols=2')
            else:
                self.origin.Execute(
                    'newsheet name:=ImportInfo cols:=2'
                )

            self.origin.Execute('wks.nrows=0')

            if not self.do_empty_data:
                self.origin.PutWorksheet(
                    'ImportInfo',
                    [[str(self.start_time), str(self.end_time)]],
                    0, 0
                )

            self.origin.Execute('col(1)[L]$ = Start time')
            self.origin.Execute('col(2)[L]$ = End time')

            self.origin.Execute('wks.labels(L)')
            self.origin.Execute('wautosize')

            # Save output file
            self.add_runtime_message("Saving output file...")
            if not self.origin.Execute(f'save {self.save_file}'):
                self.logging.error("Could not save output file.")
                raise RuntimeError("Error saving output file")

            self.add_runtime_message("Import complete!")

        except RuntimeError:
            self.add_runtime_message("Import failed!")
        finally:
            self.add_runtime_message("Closing Origin...")

            try:
                self.origin.Exit()
            except TypeError:
                pass
            finally:
                del self.origin

            t = tm.time() - t
            self.add_runtime_message(f'Done. (Total time: {t:.4f} s)')
            self.clear_file_logger()


def run_origin_import(**kwargs):
    '''Starts the origin import gui

    Allowed kwargs:
        template_file   string Origin template file
        start_time      datetime object
        end_time        datetime object
    '''

    argv = []
    app = QApplication(argv)
    form = OriginImportGui(**kwargs)
    form.show()
    app.exec_()
