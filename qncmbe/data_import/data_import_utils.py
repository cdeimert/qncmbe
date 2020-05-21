# qncmbe imports
from .core import DataCollector
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

    pass  # TODO: implement for backwards compatibility

    # local_value_names = {
    #     "Molly": [],
    #     "BET": [],
    #     "SVT": []
    # }
    # for val in value_names_list:
    #     if val not in value_names_database:
    #         raise Exception(
    #             f'Invalid value "{val}" in value_names_list. Not found in '
    #             'value_names_database'
    #         )
    #     local_value_names[value_names_database[val]['Location']].append(
    #         value_names_database[val]['Local value name']
    #     )

    # # Generate dictionary of data for each location

    # Molly_data = get_Molly_data(
    #     start_time, end_time, local_value_names["Molly"], delta_t, interp
    # )
    # BET_data = get_BET_data(start_time, end_time, local_value_names["BET"])
    # SVT_data = get_SVT_data(start_time, end_time, local_value_names["SVT"])

    # # Generate dictionary of all data
    # data = {**Molly_data, **BET_data, **SVT_data}

    # # Convert from local value names to readable value names
    # for val in value_names_list:
    #     data[val] = data.pop(value_names_database[val]['Local value name'])

    # return data

