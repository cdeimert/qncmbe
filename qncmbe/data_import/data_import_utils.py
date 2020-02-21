
# Standard library imports (not included in setup.py)
import datetime
import os
import re
import struct
from copy import deepcopy
import textwrap

# qncmbe imports
from .value_names import value_names_database

# Non-standard library imports (included in setup.py)
import numpy as np
import matplotlib.dates as mdates


class DataElement():
    '''Generic container for time-dependent data.

    Members:
        name        unique name identifying the data type
        time        numpy array of time values (in seconds)
        vals        numpy array of data values
        datetime0   datetime at which t=0
        units       string giving units of the data array

    Provides method for saving to csv and re-loading.
    '''

    def __init__(
        self, name, datetime0, time=np.zeros(0), vals=np.zeros(0)
    ):
        self.name = name
        self.datetime0 = datetime0
        self.time = time
        self.vals = vals

        if name not in value_names_database:
            raise ValueError("Data name not in value_names_database")

        self.units = value_names_database[name]['units']

    def append(self, other):
        '''Append one DataElement to another. Automatically adjusts the added
        time array based on datetime0 values.'''

        if (self.name != other.name) or (self.units != other.units):
            raise ValueError("Incompatible DataElement for appending")

        original_datetime0 = deepcopy(self.datetime0)

        # Move datetime0 so time arrays are compatible
        self.set_datetime0(other.datetime0)

        self.set_data(
            time=np.append(self.time, other.time),
            vals=np.append(self.vals, other.vals)
        )

        # Move back datetime0
        self.set_datetime0(original_datetime0)

    def set_data(self, time, vals):
        self.time = time
        self.vals = vals
        self.sort()

    def sort(self):
        '''Sort so time array is ascending'''
        mask = np.argsort(self.time)
        self.time = self.time[mask]
        self.vals = self.vals[mask]

    def trim(self, start_time, end_time):

        ti = (start_time - self.datetime0).total_seconds()
        tf = (end_time - self.datetime0).total_seconds()

        mask = (self.time >= ti) & (self.time <= tf)

        vi = self.step_interpolate(ti)
        vf = self.step_interpolate(tf)

        self.time = np.concatenate(([ti], self.time[mask], [tf]))
        self.vals = np.concatenate(([vi], self.vals[mask], [vf]))

    def step_interpolate(self, time_interp):

        inds = np.digitize(time_interp, self.time) - 1

        return self.vals[inds]

    def set_datetime0(self, datetime0):

        self.time += (self.datetime0 - datetime0).total_seconds()
        self.datetime0 = datetime0

    def save(self, savedir):

        if not os.path.exists(savedir):
            os.makedirs(savedir)

        datetime0_str = self.datetime0.strftime(r'%Y-%m-%d %H:%M:%S.%f')

        fname = os.path.join(savedir, self.get_fname())

        header = textwrap.dedent(
            f'''\
            (time=0 at: {datetime0_str})
            time (s), {self.name} ({self.units})'''
        )

        np.savetxt(
            fname=fname, X=np.c_[self.time, self.vals], header=header,
            delimiter=',', encoding='utf-8-sig'
        )

    def load(self, savedir):

        fname = os.path.join(savedir, self.get_fname())

        with open(fname, 'r', encoding='utf-8-sig') as f:
            m = re.search(
                r'^# \(time=0 at: (.*?)\)$',
                f.readline()
            )

            self.datetime0 = datetime.datetime.strptime(
                m.group(1), r'%Y-%m-%d %H:%M:%S.%f'
            )

            m = re.search(
                r'^# time \(s\), (\S+?) \((.*?)\)$',
                f.readline()
            )

            self.name = m.group(1)
            self.units = m.group(2)

        fdata = np.genfromtxt(fname, delimiter=',', skip_header=2)

        self.time = fdata[:, 0]
        self.vals = fdata[:, 1]

    def get_fname(self):
        return f'{self.name}.dat'

    def plot(self, fig, ax, use_dates=True, **kwargs):

        if 'label' not in kwargs:
            kwargs['label'] = f'{self.name}'
            if self.units != '':
                kwargs['label'] += f' ({self.units})'

        if use_dates:
            t_plt = (
                np.datetime64(self.datetime0.strftime("%Y-%m-%dT%H:%M:%S.%f"))
                + self.time*np.timedelta64(1, 's')
            )
        else:
            t_plt = self.time

        ax.step(t_plt, self.vals, where='post', **kwargs)

        if use_dates:
            ax.format_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S.%f')
            fig.autofmt_xdate()

        ax.legend()

        if use_dates:
            xlabel = ''
        else:
            xlabel = 'Time (s)'

        ax.set_xlabel(xlabel)


class DataCollector():
    def __init__(self, start_time, end_time, names, savedir=None):
        '''Generic object for collecting time-dependent data from lab computers.

        Attributes:
            start_time  datetime object. Can be initialized via string of
                        format "YYYY-mm-dd[ HH:MM[:SS]]"
            end_time    datetime object. Can be initialized via string of
                        format "YYYY-mm-dd[ HH:MM[:SS]]"
            names       list of data elements to collect. Must correspond to
                        entries in value_names_database. See
                        value_names.print_allowed_value_names()
            parameters  parameters used for data collection. Taken from the
                        value_names_database
            savedir     directory in which to save/load results after initially
                        fetching them from the remote source.
        '''

        self.start_time = DataCollector.parse_datetime_input(start_time)
        self.end_time = DataCollector.parse_datetime_input(end_time)

        if end_time <= start_time:
            raise ValueError(
                "Start time must be before end time."
            )

        self.names = names

        self.parameters = {
            name: value_names_database[name]['parameters'] for name in names
        }

        self.data = {
            name: DataElement(name, start_time) for name in self.names
        }

        self.savedir = savedir

    def collect_data(self):
        '''Collect data from remote source. Must be filled in for child class.
        '''
        return self.data

    def get_data(self, force_reload=False):
        '''Get data. Uses the collect_data() method to collect from remote
        source. If self.savedir is set, will automatically save/load from
        this local folder so that the remote data only has to be accessed
        once.'''

        if self.savedir is None:
            self.collect_data()
        else:
            if force_reload:
                self.collect_data()
                self.save_data()
            else:
                try:
                    self.load_data()
                    print(
                        "Loaded from local save data."
                    )

                except FileNotFoundError:
                    print(
                        "Local save data not found or incomplete."
                        " Loading from remote source..."
                    )
                    self.collect_data()
                    self.save_data()

        return self.data

    def generate_save_subdirname(self):

        ti_str = self.start_time.strftime(r'%Y-%m-%d_%H-%M-%S')
        tf_str = self.end_time.strftime(r'%Y-%m-%d_%H-%M-%S')

        return f'{ti_str}_to_{tf_str}'

    def save_data(self):
        '''Save all data arrays to csv files.

        These are placed in self.savedir, in a subdirectory automatically
        generated based on the start and end timestamps
        '''
        if self.savedir is None:
            raise ValueError("savedir not set.")

        subdir = os.path.join(self.savedir, self.generate_save_subdirname())
        for name, data_element in self.data.items():
            data_element.save(subdir)

    def load_data(self):
        '''Loads data from csvs. self.savedir must be set, and self.save_data()
        must have been called previously.'''

        if self.savedir is None:
            raise ValueError("savedir not set.")

        subdir = os.path.join(self.savedir, self.generate_save_subdirname())
        for name, data_element in self.data.items():
            data_element.load(subdir)

    def parse_datetime_string(datetime_string):
        '''Converts string "YYYY-mm-dd[ HH:MM[:SS]]" into datetime.datetime
        object. If optional quantities (denoted by []) are missing, they are
        set to zero. Seconds are rounded *down* to the nearest microsecond.
        '''

        result = re.match(
            r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
            r"( (?P<hour>\d{2}):(?P<minute>\d{2})"
            r"(:(?P<second>\d{2})(\.(?P<microsecond>\d+))?)?)?$",
            datetime_string
        )

        if not result:
            raise ValueError(
                'Invalid datetime string. Should be "YYYY-mm-dd[ HH:MM[:SS]]"')

        argnames = [
            'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond'
        ]

        args = {}

        for name in argnames:
            if result[name] is not None:
                if name == 'microsecond':
                    args[name] = int(float(f'0.{result[name]}')*1e6)
                else:
                    args[name] = int(result[name])

        return datetime.datetime(**args)

    def parse_datetime_input(datetime_input):
        '''Converts datetime_input into a datetime.datetime object.

        Allowed input types
        datetime.datetime object
            --> returned directly
        datetime.date object
            --> returned as datetime.datetime with time set to 00:00:00.00
        string of the form "YYYY-mm-dd[ HH:MM[:SS]]"
            --> returned as datetime.datetime object. See
                parse_datetime_string()
        '''

        if isinstance(datetime_input, str):
            return DataCollector.parse_datetime_string(datetime_input)
        elif isinstance(datetime_input, datetime.datetime):
            return datetime_input
        elif isinstance(datetime_input, datetime.date):
            time = datetime.time(0, 0, 0)
            return datetime.datetime.combine(datetime_input, time)
        else:
            raise ValueError(
                'Invalid datetime input. Should be string like'
                ' "YYYY-mm-dd[ HH:MM[:SS]]" or datetime.datetime object.'
            )

    def check_names(self, location):
        for name in self.names:
            if name not in value_names_database:
                raise ValueError(
                    f'Value name {name} not in value_names_database.'
                )
            if value_names_database[name]['location'] != location:
                raise ValueError(
                    f'Value name {name} has incorrect location for collector.'
                )


class MollyDataCollector(DataCollector):

    def __init__(self, start_time, end_time, names, savedir=None):

        super().__init__(start_time, end_time, names, savedir)

        self.check_names(location='Molly')

        self.main_data_path = os.path.join(
            r"\\insitu1.nexus.uwaterloo.ca", "Documents", "QNC MBE Data",
            "Production Data", "Molly data"
        )

    def collect_data(self):

        # For speed. Avoid touching remote files if no names are requested.
        if not self.names:
            pass

        self.data = {
            name: DataElement(name, self.start_time) for name in self.names
        }

        delta = datetime.timedelta(hours=1)

        hour = self.start_time.replace(minute=0, second=0, microsecond=0)

        '''
        Start with the previous hour to be safe.

        In principle, this shouldn't be necessary, but there are weird edge
        cases because Molly only stores a value every time the value
        *changes*. E.g., if you're loading the data for hour 02:00:00, and
        the last time the value changed was at 01:59:57, then Molly might not
        include that in the 02:00:00 hour data file. However, if the last
        time the value changed was a long time before, then Molly *does*
        include it in the data file (sometimes as a negative time). I don't
        really get the logic, but it seems that including the extra hour
        makes things safer. I hope.
        '''
        hour -= delta

        while(hour <= self.end_time + delta):

            data_hour = self.get_data_from_binary(hour)

            for name in self.names:
                self.data[name].append(data_hour[name])

            hour += delta

        # Cleanup data based on start time and end time
        for name in self.names:
            self.data[name].set_datetime0(self.start_time)
            self.data[name].trim(self.start_time, self.end_time)

        return self.data

    def get_data_path(self, hour):
        '''
        Find the path for the Molly binary file and corresponding header file
        for a given hour.
        '''

        subfolder = hour.strftime("%Y")
        subsubfolder = hour.strftime("%m-%b")
        header_filename = hour.strftime("%dday-%Hhr.txt")
        binary_filename = hour.strftime("%dday-%Hhr-binary.txt")

        header_path = os.path.join(
            self.main_data_path, subfolder, subsubfolder, header_filename
        )
        binary_path = os.path.join(
            self.main_data_path, subfolder, subsubfolder, binary_filename
        )

        return header_path, binary_path

    def get_line_numbers(self, header_path):
        '''Searches the Molly header file for self.names and returns their
        location and size in the binary file as dictionaries.
        '''

        try:
            header = open(header_path, "r")
        except IOError:
            print("Warning: missing header file " + header_path)
            return -1, -1

        try:
            total_values = {}
            values_offset = {}
            local_name = {}
            found = {}
            regex = {}
            for name in self.names:
                total_values[name] = 0
                values_offset[name] = 0
                local_name[name] = self.parameters[name]['local_name']
                found[name] = False
                regex[name] = re.compile(
                    r"^DataItem=Name:"
                    + local_name[name] + ".*?" +
                    "TotalValues:([0-9].*?);ValueOffset:([0-9].*?)\s*?\n"
                )

            for line in header:
                for name in self.names:
                    if local_name[name] in line:  # (Redundant, but faster)
                        match = regex[name].search(line)
                        if (match):
                            total_values[name] = int(match.group(1))
                            values_offset[name] = int(match.group(2))
                            if found[name]:
                                print(
                                    f"Warning: duplicate entries for '{name}'."
                                )
                            else:
                                found[name] = True

            for name in self.names:
                if not found[name]:
                    print(f"Warning: could not find value '{name}'")

        finally:
            header.close()

        return total_values, values_offset

    def get_data_from_binary(self, hour):
        '''
        Gets data from Molly binary files for a single hour.
        'hour' should be a datetime object.

        Returns a dictionary of DataElement objects (keys are self.names)

        Explanation:
        Molly data is stored in one hour chunks, sorted by date.
        E.g. /2019/08-Aug/16day-21hr-binary.txt
        There is a corresponding header file in plaintext
        E.g. /2019/08-Aug/16day-21hr.txt
        This tells you how to read the binary file.

        Values are only stored when they change. (And it checks for changes
        every ~2s) So, e.g., when Molly detects an Al base temperature changes,
        it adds a pair of values: the time it changed (relative to midnight
        that day) and the value it changed to.

        So every hour, each data signal ends up with its own list of times and
        values. The header file essentially tells you what order the values are
        in, and how many values there were that hour. Then you can go through
        the binary file sequentially to get the values.
        '''

        header_path, binary_path = self.get_data_path(hour)

        total_values, values_offset = self.get_line_numbers(header_path)

        datetime0 = hour.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            binary = open(binary_path, "rb")
        except IOError:
            print("Warning: missing binary file " + binary_path)
            return {name: DataElement(name, datetime0) for name in self.names}

        try:

            data_hour = {}
            for name in self.names:
                if (total_values[name] < 0) or (values_offset[name] < 0):
                    print(
                        "Warning: Invalid total_values or values_offset for ",
                        name
                    )
                    data_hour[name] = DataElement(name, datetime0)
                    break

                data_hour[name] = DataElement(
                    name=name, datetime0=datetime0,
                    time=np.zeros(total_values[name]),
                    vals=np.zeros(total_values[name])
                )

                binary.seek((values_offset[name]+1)*8)
                for n in range(total_values[name]):
                    data_hour[name].time[n] = struct.unpack(
                        'f', binary.read(4))[0]*86400
                    data_hour[name].vals[n] = struct.unpack(
                        'f', binary.read(4)
                    )[0]

        finally:
            binary.close()

        return data_hour


class BETDataCollector(DataCollector):
    '''For collecting data from the band-edge thermometer (BET) software.'''
    def __init__(self, start_time, end_time, names, savedir=None):

        super().__init__(start_time, end_time, names, savedir)

        self.check_names(location='BET')

        self.folders = {}

        self.main_data_path = os.path.join(
            r"\\insitu1.nexus.uwaterloo.ca", "Documents", "QNC MBE Data",
            "Production Data"
        )

    def collect_data(self):
        '''Collects data from the "BET data" and "ISP data" folders.
        Automatically determines which files to use include on the creation and
        modification times.'''

        # For speed. Avoid touching remote files if no names are requested.
        if not self.names:
            pass

        self.data = {
            name: DataElement(name, self.start_time) for name in self.names
        }

        # Loop through files. Add as necessary
        folder_set = {self.parameters[name]['folder'] for name in self.names}

        for folder in folder_set:
            folderpath = os.path.join(self.main_data_path, folder)
            for fname in os.listdir(folderpath):
                fpath = os.path.join(folderpath, fname)
                if self.is_data_file(fpath):
                    file_arr = np.loadtxt(fpath, skiprows=1)
                    file_ctime = datetime.datetime.fromtimestamp(
                        os.path.getctime(fpath)
                    )
                    for name in self.names:
                        if folderpath.endswith(
                            self.parameters[name]['folder']
                        ):

                            col = self.parameters[name]['column']
                            tcol = self.parameters[name]['time_column']

                            self.data[name].append(
                                DataElement(
                                    name=name,
                                    datetime0=file_ctime,
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

        ctime = datetime.datetime.fromtimestamp(os.path.getctime(fpath))
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))

        time_condition = (
            (self.start_time < mtime) and (self.end_time > ctime)
        )

        basename = os.path.basename(fpath)

        name_condition = (
            (basename.startswith('BET') or basename.startswith('ISP'))
            and basename.endswith('.dat')
        )

        return (time_condition and name_condition)


class SVTDataCollector(DataCollector):
    def __init__(self, start_time, end_time, names, savedir=None):

        super().__init__(start_time, end_time, names, savedir)

        self.check_names(location='SVT')

        self.main_data_path = "\\\\zw-xp1\\QNC_MBE_Data"

    def collect_data(self):

        # For speed. Avoid touching remote files if no names are requested.
        if not self.names:
            pass

        self.data = {
            name: DataElement(name, self.start_time) for name in self.names
        }

        for fname in os.listdir(self.main_data_path):
            fpath = os.path.join(self.main_data_path, fname)
            if SVTDataCollector.is_SVT_folder(fpath):

                # Check if folder has data within the requested time span,
                # otherwise skip it

                t0, ts, te = self.get_SVT_folder_time_info(fpath)

                f_zero_time = t0
                f_start_time = ts
                f_end_time = te

                time_condition = (
                    (self.end_time >= f_start_time)
                    and (self.start_time <= f_end_time)
                )

                if time_condition:

                    for name in self.names:
                        postfix = self.parameters[name]['filename']
                        col = self.parameters[name]['column']
                        tcol = self.parameters[name]['time_column']

                        basename = None
                        for bn in os.listdir(fpath):
                            if bn.endswith(postfix):
                                basename = bn
                                break

                        f_arr = SVTDataCollector.read_SVT_data_file(
                            filepath=os.path.join(fpath, basename),
                            cols=[tcol, col],
                            try_increments=True
                        )

                        self.data[name].append(
                            DataElement(
                                name=name,
                                datetime0=f_zero_time,
                                time=f_arr[:, 0]*3600*24,
                                vals=f_arr[:, 1]
                            )
                        )

        for name in self.names:
            self.data[name].trim(self.start_time, self.end_time)

        return self.data

    @staticmethod
    def is_SVT_folder(folder):
        '''
        Checks if the given folder is a valid SVT data folder
        '''

        if os.path.exists(os.path.join(folder, 'time_info.txt')):
            return True

        engine = False
        temp = False
        refl = False

        try:
            for name in os.listdir(folder):
                if name.endswith('Engine 1.txt'):
                    engine = True
                if name.endswith('IS4K Temp.txt'):
                    temp = True
                if name.endswith('IS4K Refl.txt'):
                    refl = True
        except NotADirectoryError:
            pass

        return all([engine, temp, refl])

    @staticmethod
    def get_SVT_folder_time_info(folder):
        '''
        Looks at an SVT data ouput folder to figure out the timestamp of the
        data.

        Returns 3 datetime objects.
        - t_zero: date + time corresponding to t=0 in the data file
        - t_start: date + time of the first data point
        - t_end: date + time of the last data point
        '''

        time_file = os.path.join(folder, 'time_info.txt')

        fmt_string = "%Y-%m-%d %H:%M:%S.%f"

        line0 = (
            "(Generated by Python qncmbe data_import module. Do not modify.)\n"
        )
        line1 = f'Parent folder = "{folder}"\n'

        try:
            with open(time_file) as tf:
                if tf.readline() != line0:
                    raise ValueError
                if not tf.readline().startswith('Parent folder = '):
                    raise ValueError

                arr = []
                for n in range(3):
                    date_string = tf.readline().split(' = ')[-1].strip('\n')
                    arr.append(
                        datetime.datetime.strptime(date_string, fmt_string)
                    )

                t_zero, t_start, t_end = arr

        except (FileNotFoundError, ValueError):
            data = get_SVT_data_from_folder(folder)

            t = data['SVT Time (RoboMBE Engine)']

            engine_file = ''
            for name in os.listdir(folder):
                if name.endswith('Engine 1.txt'):
                    engine_file = os.path.join(folder, name)

            # Times are just relative to midnight on some day.
            # So compare with the file creation date to figure out which day.

            creation_time = datetime.datetime.fromtimestamp(
                os.path.getctime(engine_file)
            )

            t_zero = creation_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            diff = (
                t_zero + datetime.timedelta(seconds=t[0]) - creation_time
            ).total_seconds()

            while abs(diff) > 86400/2:
                t_zero -= np.sign(diff)*datetime.timedelta(seconds=86400)

                diff = (
                    t_zero + datetime.timedelta(seconds=t[0]) - creation_time
                ).total_seconds()

            t_start = t_zero + datetime.timedelta(seconds=t[0])
            t_end = t_zero + datetime.timedelta(seconds=t[-1])

            with open(time_file, 'w') as tf:
                tf.write(line0)
                tf.write(line1)
                tf.write(f'Zero_time = {t_zero.strftime(fmt_string)}\n')
                tf.write(f'Data_start_time = {t_start.strftime(fmt_string)}\n')
                tf.write(f'Data_end_time = {t_end.strftime(fmt_string)}')

        return t_zero, t_start, t_end

    @staticmethod
    def read_SVT_data_file(filepath, cols, try_increments=True):
        '''
        Reads a single SVT data file. E.g., "G0123_IS4K Refl.txt".

        If try_increments is True, then will automatically search for
        incremented files like "G0123_IS4K Refm.txt" and get the data from them
        too. This is useful since the SVT software's default behaviour is to
        switch to a new file if the first one gets too long.

        Returns data as-is from the file. E.g., time is given in day fraction
        rather than seconds
        '''

        data = []
        name = filepath
        keep_going = True
        while keep_going:
            print(name)
            with open(name) as f:
                for line in f:
                    try:
                        data.append([float(line.split()[i]) for i in cols])
                    except (ValueError, IndexError):
                        continue

            name = SVTDataCollector.increment_SVT_filename(name)

            if try_increments:
                keep_going = os.path.exists(name)
            else:
                keep_going = False

        return np.array(data)

    @staticmethod
    def increment_SVT_filename(filepath):

        basename = filepath.strip('.txt')
        lastchar = basename[-1]

        return basename[:-1] + chr(ord(lastchar) + 1) + '.txt'


def get_data(start_time, end_time, value_names_list, delta_t=-1, interp=False):
    '''Primary function for getting data from various computers in the
    QNC-MBE lab.

    - start_time and end_time should be datetime objects.
    - value_names_list should be a list of strings. They must correspond to
      entries in the first column of value_names_database.csv
    - delta_t should be the desired time resolution of Molly data in seconds.
    - interp is a bool determining whether to linearly interpolate (True) or
      step interpolate (False) the data

    Returns 'data': a dictionary of numpy arrays, with keys corresponding to
    the value_names_list

    SPECIAL CASE:
    If delta_t == -1, raw Molly data is returned.

    Molly data is stored only when the value changes.
    Molly checks each signal for changes every 2s, and if the value doesn't
    change, it doesn't store anything. (Mostly...) Every time the value does
    change, we get a new pair of values: the time it changed, and the value it
    changed to.

    So, for raw Molly data, each data array has its own time array, which is a
    list of all the times Molly detected a change in that signal.

    In this case "Molly time" is not returned as a separate array.
    Rather, each Molly data signal is now a dictionary with two numpy arrays:
    one for 'time' and one for 'vals'

    So, e.g., suppose you are looking at 'Ga1 tip measured'.
    If delta_t = 2.0, then your time array would be data['Molly time']
    (equally spaced at 2s), and your values array would be
    data['Ga1 tip measured'].
    If delta_t = -1, then your time array would be
    data['Ga1 tip measured']['time'] and your values array would be
    data['Ga1 tip measured']['vals'].
    '''

    local_value_names = {
        "Molly": [],
        "BET": [],
        "SVT": []
    }
    for val in value_names_list:
        if val not in value_names_database:
            raise Exception(
                f'Invalid value "{val}" in value_names_list. Not found in '
                'value_names_database'
            )
        local_value_names[value_names_database[val]['Location']].append(
            value_names_database[val]['Local value name']
        )

    # Generate dictionary of data for each location

    Molly_data = get_Molly_data(
        start_time, end_time, local_value_names["Molly"], delta_t, interp
    )
    BET_data = get_BET_data(start_time, end_time, local_value_names["BET"])
    SVT_data = get_SVT_data(start_time, end_time, local_value_names["SVT"])

    # Generate dictionary of all data
    data = {**Molly_data, **BET_data, **SVT_data}

    # Convert from local value names to readable value names
    for val in value_names_list:
        data[val] = data.pop(value_names_database[val]['Local value name'])

    return data


def get_raw_Molly_data(start_time, end_time, value_names):
    '''Gets raw Molly data (uneven timesteps, unique time array for each value)
    Since the files are stored in one-hour chunks, it loops through hour
    by hour.

    This function returns all the one-hour chunks necessary to cover start_time
    to end_time.
    It also includes an extra hour buffer on each end for safety.

    Return value is a dictionary with keys equal to value names.
    Each dictionary element is another dictionary with two keys: 'time'
    (containing a numpy time array) and 'vals' (containing a numpy value array)
    '''

    delta = datetime.timedelta(hours=1)

    hour = start_time.replace(minute=0, second=0, microsecond=0)

    # Start with the previous hour to be safe.
    #
    # In principle, this shouldn't be necessary, but there are weird edge cases
    # because Molly only stores a value every time the value *changes*.
    # E.g., if you're loading the data for hour 02:00:00, and the last time the
    # value changed was at 01:59:57, then Molly might not include that in the
    # 02:00:00 hour data file. However, if the last time the value changed was
    # a long time before, then Molly *does* include it in the data file
    # (sometimes as a negative time). I don't really get the logic, but it
    # seems that including the extra hour makes things safer. I hope.
    hour -= delta

    # Since Molly time is relative to midnight, need to manually keep track of
    # the days
    start_day = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day = hour.replace(hour=0, minute=0, second=0, microsecond=0)

    data = {}

    while(hour <= end_time + delta):

        data_hour = get_raw_Molly_data_hour(hour, value_names)

        num_days = (day - start_day).days

        for name in value_names:

            # if data_hour[name]['time'][0]

            data_hour[name]['time'] += num_days*86400

            if (name not in data):
                data[name] = {'time': [], 'vals': []}

            data[name]['time'].append(data_hour[name]['time'])
            data[name]['vals'].append(data_hour[name]['vals'])

        hour += delta

        day = hour.replace(hour=0, minute=0, second=0, microsecond=0)

    # Concatenate so that all the data is in one list
    for name in value_names:
        data[name]['time'] = np.concatenate(data[name]['time'])
        data[name]['vals'] = np.concatenate(data[name]['vals'])

    return data


def get_Molly_data(start_time, end_time, value_names, delta_t, interp=False):

    if not value_names:
        return {}  # Redundant, but increases speed.

    # Create list of values with "Time" excluded.
    raw_value_names = list(value_names)
    while "Time" in raw_value_names:
        raw_value_names.remove("Time")

    # Get raw values (not interpolated)
    raw_data = get_raw_Molly_data(start_time, end_time, raw_value_names)

    # Shift raw data time so that zero corresponds to start time.
    # (Time vectors from get_raw_Molly_data() are in "Molly time", zero is
    # midnight on the first day.)
    molly_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

    for name in raw_value_names:
        raw_data[name]['time'] = raw_data[name]['time'] - \
            (start_time - molly_time).total_seconds()

    # Find total number of seconds between start and end time
    tot_seconds = (end_time - start_time).total_seconds()

    if delta_t == -1:
        # If delta_t is -1, then return the raw data without interpolating
        # In this case, there will be a separate time array associated with
        # each value

        data = {}
        for name in raw_value_names:

            inds = (raw_data[name]['time'] >= 0) & (
                raw_data[name]['time'] <= tot_seconds)
            data[name] = {
                'time': raw_data[name]['time'][inds],
                'vals': raw_data[name]['vals'][inds]
            }

        return data

    # Create interpolated time vector so that all values share the same time.
    # arange excludes the endpoint by default. The 1e-3*delta_t buffer is a
    # "safety" for that
    time_interp = np.arange(0.0, tot_seconds + 1e-3*delta_t, delta_t)

    data = {}
    for name in raw_value_names:

        if raw_data[name]['vals'].size == 0:
            # If the value was not found, return a list of NaNs.
            data[name] = np.empty_like(time_interp)
            data[name][:] = np.nan

        else:
            # interp decides whether the data should be linearly interpolated
            # or step interpolated
            if interp:
                data[name] = np.interp(
                    time_interp, raw_data[name]['time'], raw_data[name]['vals']
                )
            else:
                # Have to sort the raw data so that the times are
                # monotonically-increasing... They should be monotonically-
                # increasing anyway, but it seems like rounding error sometimes
                # screws this up.
                sort_inds = np.argsort(raw_data[name]['time'])
                raw_data[name]['time'] = raw_data[name]['time'][sort_inds]
                raw_data[name]['vals'] = raw_data[name]['vals'][sort_inds]

                # Now, for each time in the interpolated data, find the last
                # time in the raw data that the value was changed, and use the
                # corresponding value.
                inds = np.digitize(time_interp, raw_data[name]['time']) - 1
                data[name] = raw_data[name]['vals'][inds]

    if "Time" in value_names:
        data["Time"] = time_interp

    return data


def get_SVT_data_from_folder(folder, time_limits=None):

    col_info = {
        'Engine 1.txt': {
            'SVT Time (RoboMBE Engine)': 0,
            'PI 950': 1,
            'PI 850': 2,
            'Refl 950': 3,
            'Refl 470': 4
        },
        'IS4K Temp.txt': {
            'SVT Time (RoboMBE IS4K Temp)': 0,
            'Emiss Temp': 3,
            'Ratio Temp': 2
        },
        'IS4K Refl.txt': {
            'SVT Time (RoboMBE IS4K Refl)': 0,
            'Calib 950': 1,
            'Calib 470': 2
        }
    }

    data = {}
    for name in os.listdir(folder):
        full_name = os.path.join(folder, name)

        for basename in col_info:
            if name.endswith(basename):

                keys = []
                cols = []

                for k, c in col_info[basename].items():
                    keys.append(k)
                    cols.append(c)

                fdata = SVTDataCollector.read_SVT_data_file(
                    full_name, cols, True
                )

                for n, k in enumerate(keys):
                    data[k] = fdata[:, n]

    for key in data:
        if 'Time' in key:
            data[key] *= 3600*24

    if time_limits is not None:
        t_min = time_limits[0]
        t_max = time_limits[1]
        for basename in col_info:
            for key in col_info[basename]:
                if 'Time' in key:
                    time_key = key

                t = data[time_key]

            mask = (t >= t_min) & (t <= t_max)
            for key in col_info[basename]:
                data[key] = data[key][mask]

    return data
