# qncmbe imports
from .core import DataCollector
from .molly import MollyDataCollector
from .BET import BETDataCollector
from .SVT import SVTDataCollector
from .data_names import index

# Non-standard library imports (included in setup.py)
# import numpy as np


class GrowthDataCollector(DataCollector):
    '''Class to collect multiple kinds of data, related to MBE growths.'''

    def __init__(self, start_time, end_time, names, savedir=None):

        super().__init__(start_time, end_time, names, savedir)

        # Sort through names, and split into Molly, BET, and SVT

        self.locations = {"Molly", "BET", "SVT"}

        names_split = {location: [] for location in self.locations}

        for name in self.names:
            location = index[name]['location']
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