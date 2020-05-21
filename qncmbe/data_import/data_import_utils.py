# Standard library imports (not included in setup.py)
import datetime
import os

# qncmbe imports
from .core import DataCollector, DataElement
from .molly import MollyDataCollector
from .BET import BETDataCollector
from .SVT import SVTDataCollector
from .value_names import value_names_database

# Non-standard library imports (included in setup.py)
import numpy as np


class GrowthDataCollector(DataCollector):
    '''Class to collect multiple kinds of data, related to MBE growths.'''

    def __init__(self, start_time, end_time, names, savedir=None):

        super().__init__(start_time, end_time, names, savedir)

        # Sort through names, and split into Molly, BET, and SVT

        self.locations = {"Molly", "BET", "SVT"}

        names_split = {location: [] for location in self.locations}

        for name in self.names:
            location = value_names_database[name]['location']
            names_split[location].append(name)

        DataCollectors = {
            "Molly": MollyDataCollector,
            "BET": BETDataCollector,
            "SVT": SVTDataCollector
        }

        self.collectors = {
            location: DataCollectors[location](
                start_time,
                end_time,
                names_split[location],
                savedir
            ) for location in self.locations
        }

    def collect_data(self):

        for location in self.locations:
            self.data.update(self.collectors[location].collect_data())

        return self.data


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

