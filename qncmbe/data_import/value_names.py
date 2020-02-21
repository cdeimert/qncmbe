# Standard library imports (not included in setup.py)
# from collections import OrderedDict
import csv
import os.path as path


thisdir = path.dirname(path.abspath(__file__))
database_file = path.join(thisdir, 'value_names_database.csv')

reader = csv.DictReader(open(database_file, 'rt', encoding="utf-8-sig"))

value_names_database = {}

for line in reader:

    location = line['location']
    name = line['name']
    exec('parameters = dict(' + line['parameters'].replace(';', ',') + ')')
    units = line['units']

    value_names_database[name] = {
        'location': location,
        'parameters': parameters,
        'units': units,
    }


def print_allowed_value_names(full_csv=False):

    if full_csv:
        with open(database_file, 'r', encoding="utf-8-sig") as f:
            out_str = f.read()
    else:
        out_str = ''
        for vn in value_names_database:
            out_str += f'{vn}\n'

    print(out_str)

    return out_str


def get_value_names_list(location="all"):
    '''Gets a list of all value names from the value names database if
    location == "all". Otherwise, only returns value names from a particular
    location (either "Molly", "SVT", or "BET")
    '''

    value_names_list = []
    for val in value_names_database:
        if (
            (location == "all") or
            (location == value_names_database[val]["location"])
        ):
            value_names_list.append(val)

    return value_names_list
