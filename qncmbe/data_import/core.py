# Standard library imports (not included in setup.py)
import datetime
import os
import re
from copy import deepcopy
import textwrap

# qncmbe imports
from .value_names import value_names_database

# Non-standard library imports (included in setup.py)
import numpy as np
import matplotlib.dates as mdates
from dateutil import parser as date_parser


class DataElement():
    '''Generic container for time-dependent data.

    Members:
        name            unique name identifying the data type
        time            numpy array of time values (in seconds)
        vals            numpy array of data values
        datetime0       datetime at which t=0
        units           string giving units of the data array
        is_step_data    bool

    Provides method for saving to csv and re-loading.

    Notes:
        - The time array is sorted in set_data(), and it should remain sorted
        - For now, it is assumed vals is a 1D array of the same length as time
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
        '''Set the time and vals members, and also sort them'''

        if len(time) != len(vals):
            raise ValueError("time and vals must have the same length.")

        self.time = np.array(time)
        self.vals = np.array(vals)
        self.sort()

    def sort(self):
        '''Sort both time and vals so that the time array is ascending'''
        mask = np.argsort(self.time)
        self.time = self.time[mask]
        self.vals = self.vals[mask]

    def trim(self, start_time, end_time, include_endpoints=False):
        '''
        Remove all data before start_time and after end_time (both should be
        datetime objects).

        if include_endpoints is True, will explicitly add data points at
        start_time and end_time. (May be important for stepped data with long
        gaps between time points.)
        '''

        # In case of empty array, do nothing
        if len(self.vals) == 0:
            return

        ti = (start_time - self.datetime0).total_seconds()
        tf = (end_time - self.datetime0).total_seconds()

        if include_endpoints:
            mask = (self.time > ti) & (self.time < tf)
            # Don't want endpoints here since they will be explicitly included
            # later
        else:
            mask = (self.time >= ti) & (self.time <= tf)

        new_time = self.time[mask]
        new_vals = self.vals[mask]

        if include_endpoints:
            vi = self.step_interpolate(ti)
            vf = self.step_interpolate(tf)

            new_time = np.append(new_time, tf)
            new_vals = np.append(new_vals, vf)

            new_time = np.insert(new_time, 0, ti)
            new_vals = np.insert(new_vals, 0, vi)

        self.set_data(new_time, new_vals)

    def step_interpolate(self, time_interp):

        if len(self.vals) == 0:
            return np.array([])
        else:
            inds = np.digitize(time_interp, self.time) - 1

            if np.isscalar(inds):
                if inds < 0:
                    inds = 0
            else:
                inds[inds < 0] = 0

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

        if fdata.size == 0:
            self.time = np.array([])
            self.vals = np.array([])
        else:
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
        '''Generic class for collecting time-dependent data from lab computers.

        Attributes:
            start_time  datetime object. Can initialize with string (see note)
            end_time    datetime object. Can initialize with string (see note)
            names       list of data elements to collect. Must correspond to
                        entries in value_names_database. See
                        value_names.print_allowed_value_names()
            parameters  parameters used for data collection. Taken from the
                        value_names_database
            savedir     directory in which to save/load results after initially
                        fetching them from the remote source. If None, will
                        always load from source

        Note: start_time and end_time can be initialized with strings (although
        they will be stored as datetime objects). The dateutil.parser module
        is used, so the string format is fairly flexible.
        '''

        self.start_time = parse_datetime_input(start_time)
        self.end_time = parse_datetime_input(end_time)

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
                    print("Loaded from local save data.")

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


def parse_datetime_input(datetime_input):
    '''Converts datetime_input into a datetime.datetime object.

    Allowed input types
    datetime.datetime object
        --> returned directly
    datetime.date object
        --> returned as datetime.datetime with time set to 00:00:00.00
    datetime string
        --> returned as datetime.datetime object, using dateutil.parser
    '''

    if isinstance(datetime_input, str):
        return date_parser.parse(datetime_input)

    elif isinstance(datetime_input, datetime.datetime):
        return datetime_input

    elif isinstance(datetime_input, datetime.date):
        time = datetime.time(0, 0, 0)
        return datetime.datetime.combine(datetime_input, time)

    else:
        raise ValueError(
            'datetime_input must be datetime object or valid string.'
        )


# def parse_datetime_string(datetime_string):
#     '''Converts string "YYYY-mm-dd[ HH:MM[:SS]]" into datetime.datetime
#     object. If optional quantities (denoted by []) are missing, they are
#     set to zero. Seconds are rounded *down* to the nearest microsecond.
#     '''

#     result = re.match(
#         r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
#         r"( (?P<hour>\d{2}):(?P<minute>\d{2})"
#         r"(:(?P<second>\d{2})(\.(?P<microsecond>\d+))?)?)?$",
#         datetime_string
#     )

#     if not result:
#         raise ValueError(
#             'Invalid datetime string. Should be "YYYY-mm-dd[ HH:MM[:SS]]"')

#     argnames = [
#         'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond'
#     ]

#     args = {}

#     for name in argnames:
#         if result[name] is not None:
#             if name == 'microsecond':
#                 args[name] = int(float(f'0.{result[name]}')*1e6)
#             else:
#                 args[name] = int(result[name])

#     return datetime.datetime(**args)
