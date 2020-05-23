# Standard library imports (not included in setup.py)
import datetime
import os
import re

# qncmbe imports
from .utils import DataCollector, DataElement
from .data_names import index

# Non-standard library imports (included in setup.py)
import numpy as np
from dateutil import parser as date_parser


class BETDataCollector(DataCollector):
    '''For collecting data from the band-edge thermometer (BET) software.'''

    default_data_path = os.path.join(
        r"\\insitu1.nexus.uwaterloo.ca", "Documents", "QNC MBE Data",
        "Production Data"
    )

    def __init__(self, start_time, end_time, names, savedir=None):
        '''See docstring for parent (DataCollector)'''

        super().__init__(start_time, end_time, names, savedir)

        self.check_names(location='BET')

        self.folders = {}

        self.main_data_path = self.default_data_path

    def find_bad_data_paths(self):

        if os.path.exists(self.main_data_path):
            return []
        else:
            return [self.main_data_path]

    def collect_data(self):
        '''Collects data from the "BET data" and "ISP data" folders.
        Automatically determines which files to use include on the creation and
        modification times.'''

        self.initialize_data()

        # For speed. Skip collection process if no names are requested.
        if not self.names:
            return {}

        # Loop through files. Add as necessary
        folder_set = {self.parameters[name]['folder'] for name in self.names}

        for folder in folder_set:
            folderpath = os.path.join(self.main_data_path, folder)
            for fname in os.listdir(folderpath):
                fpath = os.path.join(folderpath, fname)
                if self.is_data_file(fpath):
                    file_arr = np.loadtxt(fpath, skiprows=1)

                    file_ctime, _ = BETDataCollector.get_file_times(fpath)

                    for name in self.names:
                        if folderpath.endswith(
                            self.parameters[name]['folder']
                        ):

                            col = self.parameters[name]['column']
                            tcol = self.parameters[name]['time_column']

                            self.data[name].add_data(
                                DataElement(
                                    name=name,
                                    datetime0=file_ctime,
                                    units=index[name].units,
                                    time=file_arr[:, tcol],
                                    vals=file_arr[:, col]
                                )
                            )

        for name in self.names:
            self.data[name].trim(self.start_time, self.end_time)

        return self.data

    def is_data_file(self, fpath):
        '''Checks the file (full path specified by fpath) to see if it contains
        relevant data. Based on self.start_time and self.end_time.'''

        ctime, mtime = BETDataCollector.get_file_times(fpath)

        time_condition = (
            (self.start_time < mtime) and (self.end_time > ctime)
        )

        basename = os.path.basename(fpath)

        name_condition = (
            (basename.startswith('BET') or basename.startswith('ISP'))
            and basename.endswith('.dat')
        )

        return (time_condition and name_condition)

    @staticmethod
    def get_file_times(fpath):
        '''Gets the creation and modification date of the BET data file.

        Tries to use the file creation time for the best precision. However,
        the file creation time could change significantly if the file is
        copied. So it is verified against the timestamp. If there is a
        conflict, the timestamp will be used (less precise).'''

        file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
        file_ctime = datetime.datetime.fromtimestamp(os.path.getctime(fpath))

        datetime_regex = (
            r"(?P<time>\d\d\.\d\d(?P<sec>.\d\d)?) "
            r"(?P<date>\w+, \w+ \d\d, \d{4})\.dat"
        )

        basename = os.path.basename(fpath)

        match = re.search(datetime_regex, basename)

        if match is None:
            raise ValueError(
                "Invalid/missing timestamp:"
                f'\n  "{fpath}"'
            )
        else:
            time_str = match.group('time').replace('.', ':')
            date_str = match.group('date')

            timestamp = date_parser.parse(f'{date_str} {time_str}')

            # Some older timestamps are missing the seconds, so need two cases
            if match.group('sec') is None:
                if abs((timestamp - file_ctime).total_seconds()) < 60:
                    ctime = file_ctime
                else:
                    ctime = timestamp
            else:
                if abs((timestamp - file_ctime).total_seconds()) < 1:
                    ctime = file_ctime
                else:
                    ctime = timestamp

        mtime = file_mtime

        return ctime, mtime

