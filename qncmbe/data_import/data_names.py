# Standard library imports (not included in setup.py)
import csv
import os.path as path
import ast
import re
import logging


logger = logging.getLogger(__name__)


class DataInfo():
    '''Info for a single data value.

    Attributes:
        display_name    Name formatted for display
        location        Where the data was generated. (E.g., "Molly", "SVT")
                        Important for deciding which DataCollector to use
        sublocation     E.g. if location is "Molly", sublocation could specify
                        which cell the data is associated with. Just useful
                        for organizing the data later.
        parameters      Additional parameters needed by the DataCollector
        units           units for display
    '''
    def __init__(
        self, name='', location='', sublocation='', parameters={}, units=''
    ):
        self.display_name = name
        self.location = location
        self.sublocation = sublocation
        self.parameters = parameters
        self.units = units

    def __str__(self):
        string = (
            f"name: {self.display_name}"
            f"\nlocation: {self.location}"
            f"\nsublocation: {self.sublocation}"
            f"\nparameters: {self.parameters}"
            f"\nunits: {self.units}"
        )

        return string


class FlexibleDict(dict):
    '''Dictionary whose keys are insensitive to case and punctuation.

    When the keys are stored/accessed, capitals are stripped away, and any
    punctuation/whitespace is replaced with a single "_". So, e.g.,

    "ThIs_, is   MY, ^^ eXamplE.*Key" is replaced with "this_is_my_example_key"

    Specifically, punctuation is done by the regex replacement '[\W_]+' --> '_'

    Note: this only applies to string keys. Numerical keys are untouched.
    '''

    _kr = re.compile('[\W_]+')

    @classmethod
    def _k(cls, key):
        return cls._kr.sub('_', key.lower()) if isinstance(key, str) else key

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super().__getitem__(type(self)._k(key))

    def __setitem__(self, key, value):
        super().__setitem__(type(self)._k(key), value)

    def __delitem__(self, key):
        return super().__delitem__(type(self)._k(key))

    def __contains__(self, key):
        return super().__contains__(type(self)._k(key))

    def pop(self, key, *args, **kwargs):
        return super().pop(type(self)._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super().get(type(self)._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super().setdefault(type(self)._k(key), *args, **kwargs)

    def update(self, E={}, **F):
        super().update(type(self)(E))
        super().update(type(self)(**F))

    def _convert_keys(self):
        for k in list(self.keys()):
            v = super().pop(k)
            self.__setitem__(k, v)


class DataNamesIndex(FlexibleDict):
    '''A dictionary of name: DataInfo() pairs.

    Extends the dictionary class to auto-initialize it based on
    data_names_index.csv and also provides useful methods, e.g.
    for getting all names at a certain location.

    Extends the dictionary class so that the keys are case insensitive and
    '.', '_', and ' ' are equivalent.
    '''

    def __init__(self):

        super().__init__()

        this_dir = path.dirname(path.abspath(__file__))
        self.database_file = path.join(this_dir, 'data_names_index.csv')

        self.read_database_file()

    def read_database_file(self):
        '''Reads the database csv file into the main dictionary

        Assumes there are four columns with headers 'name', 'location',
        'parameters', and 'units'. Columns are separated by a semicolon.

        The parameters column should be a comma-separated list of arguments
        like
            arg1=34,arg2='asdf',arg3=True
        with no spaces separating them.

        These parameters are converted into a dictionary:
        {
            'arg1': 34,
            'arg2': 'asdf',
            'arg3': True,
        }

        For security, the arguments can only be primitive types (number,
        string, bool, etc.), not, e.g., user-defined classes. They are
        evaluated by ast.literal_eval().

        Regarding strings:
          - They must be surrounded by single-quotes, not double quotes.
          - They cannot include the delimiters ,;= (this is difficult to catch
            and the script may break in unexpected ways)
        '''

        with open(self.database_file, 'rt', encoding="utf-8-sig") as df:
            reader = csv.DictReader(df, delimiter=';')

            for line in reader:

                name = line['name']
                location = line['location']
                sublocation = line['sublocation']
                units = line['units']

                parameters = {}
                for arg in line['parameters'].split(','):
                    key, val = arg.split('=')
                    parameters[key] = ast.literal_eval(val)

                if name in self:
                    raise ValueError(
                        f'Duplicate name "{name}". Check database file'
                        f' "{self.database_file}"'
                    )
                else:
                    self[name] = DataInfo(
                        name=name,
                        location=location,
                        sublocation=sublocation,
                        parameters=parameters,
                        units=units
                    )

    def get_names_list(self, location='all'):
        '''Gets a list of all value names from the value names database if
        location == "all". Otherwise, only returns value names from a
        particular location (either "Molly", "SVT", or "BET")
        '''

        names_list = []
        for name in self:
            if (
                (location == "all") or (location == self[name].location)
            ):
                names_list.append(self[name].display_name)

        return names_list

    def get_value_names_csv_as_string(self):

        with open(self.database_file, 'r', encoding="utf-8-sig") as f:
            out_str = f.read()

        return out_str


index = DataNamesIndex()


def print_allowed_value_names(full_csv=False):

    logger.warning(
        "print_allowed_value_names() is no longer maintained."
        " Use DataNamesIndex class instead.",
    )

    if full_csv:
        out_str = index.get_value_names_csv_as_string()
    else:
        out_str = index.get_names_list('all')

    print(out_str)
    return out_str


def get_value_names_list(location="all"):
    '''Gets a list of all value names from the value names database if
    location == "all". Otherwise, only returns value names from a particular
    location (either "Molly", "SVT", or "BET")
    '''

    logger.warning(
        "get_value_names_list() is no longer maintained."
        " Use DataNamesIndex.get_names_list() instead."
    )

    return index.get_names_list(location)
