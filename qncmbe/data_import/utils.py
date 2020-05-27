# Standard library imports (not included in setup.py)
import datetime
import os
import re
from copy import deepcopy
import textwrap
import logging

# qncmbe imports
from .data_names import index

# Non-standard library imports (included in setup.py)
import numpy as np
import matplotlib.dates as mdates
from dateutil import parser as date_parser


logger = logging.getLogger(__name__)

formatter = logging.Formatter('%(levelname)s: %(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

logging.getLogger().addHandler(console_handler)
logging.getLogger().setLevel(logging.INFO)


class DataElement():
    '''Generic container for time-dependent data.

    Members:
        name            unique name identifying the data type
        time            numpy array of time values (in seconds)
        vals            numpy array of data values
        datetime0       datetime at which t=0
        units           string giving units of the data array

    Provides method for saving to csv and re-loading.

    Slicing (e.g., "my_data_element[2:3]") will return a copy of the
    DataElement with both time and vals sliced appropriately.

    Assignment by slicing is not supported.

    Notes:
        - The time array is sorted in set_data(), and it should remain sorted
        - For now, it is assumed vals is a 1D array of the same length as time
    '''

    def __init__(
        self, name, datetime0, units='', time=np.zeros(0), vals=np.zeros(0)
    ):
        self.name = name
        self.datetime0 = datetime0
        self.units = units
        self.set_data(time, vals)

    def __getitem__(self, slice_):
        return DataElement(
            name=deepcopy(self.name),
            datetime0=deepcopy(self.datetime0),
            time=self.time[slice_],
            vals=self.vals[slice_],
            units=deepcopy(self.units)
        )

    def __len__(self):
        return len(self.time)

    def add_data(self, other):
        '''Add data from one DataElement to the present DataElement (still
        keeping the existing data.)

        Automatically ensures that times are consistent based on the datetime0
        of each element. Also sorts so that time is sequential.'''

        if (self.name != other.name) or (self.units != other.units):
            raise ValueError("Incompatible DataElement for addition")

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

        # Save endpoint data before trimming
        if include_endpoints:
            di = self.step_interpolate(ti)
            df = self.step_interpolate(tf)

        self.set_data(self.time[mask], self.vals[mask])

        if include_endpoints:
            self.add_data(di)
            self.add_data(df)

    def step_interpolate(self, ti, right=False):
        '''Step-interpolates the current DataElement at time values ti, and
        returns in the form of a new DataElement.

        Step interpolation means it picks the nearest time value in DataElement
        and uses the corresponding value. It rounds up or down depending on
        whether right = True or False

        So, if time = [0,1,2,3], vals = [5,7,9,11]

        ti=2.5 will return 9 if right=False, 11 if right=True
        '''
        if len(self.vals) == 0:
            return deepcopy(self)
        else:
            if np.isscalar(ti):
                ti = np.array([ti])

            if right:
                inds = np.digitize(ti, self.time, right=True)
                inds[inds >= len(self.time)] = len(self.time)-1
            else:
                inds = np.digitize(ti, self.time) - 1
                inds[inds < 0] = 0

        output = deepcopy(self)

        output.set_data(ti[:], self.vals[inds])

        return output

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
                r'^# time \(s\), (?P<name>.*?) \((?P<units>.*?)\)$',
                f.readline()
            )

            self.units = m.group('units')

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
        '''Plot data of DataElement on a matplotlib figure.

        Arguments:
            fig, ax     matplotlib Figure and Axis objects
            use_dates   If True, will use dates when plotting time. Otherwise
                        will plot time in seconds.
            kwargs      keyword arguments, passed directly to ax.step()

        If 'label' is not given explicitly as a keyword argument, the plot
        label is auto-generated based on the DataElement name and units.
        '''

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
                        entries in index. See
                        value_names.print_allowed_value_names()
            parameters  dict of parameters used for data collection. Taken from
                        data_names.index
            units       dict of units corresponding to each name. Taken from
                        data_names.index
            savedir     directory in which to save/load results after initially
                        fetching them from the remote source. If None, will
                        always load from source

        Note: start_time and end_time can be initialized with strings (although
        they will be stored as datetime objects). The dateutil.parser module
        is used, so the string format is fairly flexible.
        '''

        self.set_times(start_time, end_time, clear_data=False)

        if self.end_time <= self.start_time:
            raise ValueError(
                "Start time must be before end time."
            )

        self.set_names(names)
        # Also sets self.parameters, self.units, and initializes self.data

        self.set_savedir(savedir)

    def initialize_data(self):

        self.data = {}

        for name in self.names:
            self.data[name] = DataElement(
                name, self.start_time, self.units[name]
            )

        return self.data

    def set_names(self, names):

        self.names = names

        self.parameters = {name: index[name].parameters for name in names}
        self.units = {name: index[name].units for name in names}

        self.initialize_data()

    def set_savedir(self, savedir):
        self.savedir = savedir

    def set_times(self, start_time, end_time, clear_data=True):
        self.start_time = parse_datetime_input(start_time)
        self.end_time = parse_datetime_input(end_time)

        if clear_data:
            self.initialize_data()

    def find_bad_data_paths(self):
        '''Checks data paths. Returns list of problematic paths.
        (Returns empty list if everything is okay)
        '''
        return []

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
                    logger.info("Loaded from local save data.")

                except FileNotFoundError:
                    logger.info(
                        "Local save data unavailable or incomplete."
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
            if name not in index:
                raise ValueError(
                    f'Value name {name} not in index.'
                )
            if index[name].location != location:
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

