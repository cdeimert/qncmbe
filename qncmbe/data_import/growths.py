# Standard library imports
from pathlib import Path
import logging

# qncmbe imports
from .utils import DataCollector
from .molly import MollyDataCollector
from .BET import BETDataCollector
from .SVT import SVTDataCollector
from .data_names import index


logger = logging.getLogger(__name__)


class GrowthDataCollector(DataCollector):
    '''Class to collect multiple kinds of data, related to MBE growths.

    Currently includes Molly, BET, and SVT data.
    
    Members:
        locations       A set of all allowed location strings
        subcollectors   dictionary of DataCollectors {location: DataCollector}
    '''

    locations = {"Molly", "BET", "SVT"}

    def __init__(
        self, start_time, end_time, names, savedir=None, molly_dt=None
    ):

        self.names = names

        # Set up a data collector for each location
        collector_cls = {
            "Molly": MollyDataCollector,
            "BET": BETDataCollector,
            "SVT": SVTDataCollector
        }

        self.collectors = {}

        for location in self.locations:

            names_in_loc = self.filter_names(location)

            kwargs = {
                'start_time': start_time,
                'end_time': end_time,
                'names': names_in_loc,
                'savedir': savedir
            }

            if location == "Molly":
                kwargs['dt'] = molly_dt

            self.collectors[location] = collector_cls[location](**kwargs)

        super().__init__(start_time, end_time, names, savedir)

        # Use locally-saved data for speed during testing
        # self._set_test_mode()

    def filter_names(self, location):
        return [n for n in self.names if index[n].location == location]

    def set_names(self, names):

        super().set_names(names)
        for loc in self.locations:
            names_in_loc = self.filter_names(loc)
            self.collectors[loc].set_names(names_in_loc)

    def set_times(self, *args, **kwargs):

        super().set_times(*args, **kwargs)

        for loc in self.locations:
            self.collectors[loc].set_times(*args, **kwargs)

    def set_data_path(self, location, path):
        self.collectors[location].main_data_path = path

    def find_bad_data_paths(self):

        bad_paths = []
        for loc, coll in self.collectors.items():
            bad_paths += coll.find_bad_data_paths()

        return bad_paths

    def collect_data(self):

        self.data = {}

        for loc, coll in self.collectors.items():
            self.data.update(coll.collect_data())

        return self.data

    def _set_test_mode(self):
        '''Use locally-saved data for speed during testing.'''

        logger.warning("Using GrowthDataCollector in test mode!")

        root = Path(__file__).resolve().parent.parent.parent

        basedir = root.joinpath('tests', 'example_data')

        data_dirs = {
            "BET": basedir,
            "SVT": basedir.joinpath('SVT Data'),
            "Molly": basedir.joinpath('Molly Data')
        }

        for loc in data_dirs:
            self.set_data_path(loc, data_dirs[loc])

