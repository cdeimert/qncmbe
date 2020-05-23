from pathlib import Path

# qncmbe imports
from .utils import DataCollector
from .molly import MollyDataCollector
from .BET import BETDataCollector
from .SVT import SVTDataCollector
from .data_names import index

# Non-standard library imports (included in setup.py)
# import numpy as np


class GrowthDataCollector(DataCollector):
    '''Class to collect multiple kinds of data, related to MBE growths.

    Currently includes Molly, BET, and SVT data.'''

    locations = {"Molly", "BET", "SVT"}

    def __init__(
        self, start_time, end_time, names, savedir=None, molly_dt=None
    ):

        super().__init__(start_time, end_time, names, savedir)

        # Sort through names, and split into Molly, BET, and SVT
        names_split = {location: [] for location in self.locations}

        for name in self.names:
            location = index[name].location
            names_split[location].append(name)

        # Set up a data collector for each location
        collector_cls = {
            "Molly": MollyDataCollector,
            "BET": BETDataCollector,
            "SVT": SVTDataCollector
        }

        self.subcollectors = {}

        for location in self.locations:

            kwargs = {
                'start_time': start_time,
                'end_time': end_time,
                'names': names_split[location],
                'savedir': savedir
            }

            if location == "Molly":
                kwargs['dt'] = molly_dt

            self.subcollectors[location] = collector_cls[location](**kwargs)

        # self._set_test_mode()

    def set_data_path(self, location, path):
        self.subcollectors[location].main_data_path = path

    def find_bad_data_paths(self):

        bad_paths = []
        for loc, coll in self.subcollectors.items():
            bad_paths += coll.find_bad_data_paths()

        return bad_paths

    def collect_data(self):

        self.data = {}

        for loc, coll in self.subcollectors.items():
            self.data.update(coll.collect_data())

        return self.data

    def _set_test_mode(self):

        root = Path(__file__).resolve().parent.parent.parent

        basedir = root.joinpath('tests', 'example_data')

        data_dirs = {
            "BET": basedir,
            "SVT": basedir.joinpath('SVT Data'),
            "Molly": basedir.joinpath('Molly Data')
        }

        for loc in data_dirs:
            self.set_data_path(loc, data_dirs[loc])

