# Standard library imports (not included in setup.py)
import csv
import os.path as path
import re


thisdir = path.dirname(path.abspath(__file__))
database_file = path.join(thisdir, 'Molly_value_names.csv')

reader = csv.DictReader(open(database_file, 'rt', encoding="utf-8-sig"))

value_names_database = {}

for line in reader:
    value_names_database[line['varname']] = {
            'local_name': line['varname'],
            'units': line['units']
        }

def clean_molly_varname(varname):
    '''Converts Molly variable name into a more consistent snake case.
    
    Examples:
        Instances.Ga1_tip.WorkingSetpoint --> Ga1_tip_working_setpoint
        Instances.C1_Current.Measured --> C1_current_measured
        Instances.GaTe1_tip.Measured --> GaTe1_tip_measured
        Instances.GM1_BFM.Reading --> GM1_BFM_reading

    '''

    name = varname[:]

    # Strip 'Instances.' from beginning
    prefix = 'Instances.'
    if name.startswith(prefix):
        name = name[len(prefix):]
    else:
        raise ValueError("Invalid Molly variable name.")

    # Separate the first subname (up to the first _ or .)
    # Case should be preserved on this part, even if it looks camel case
    # (E.g. GaTe1)
    subname0 = re.split('_|\.', name)[0]

    # Now find all the remaining subnames in the remaining string
    # This time, split on camel case if it's present
    # (Acronums aren't counted as camel case)
    remainder = name[len(subname0):]

    subname_matches = re.findall(
        f'(([A-Z]+|[a-z])([^A-Z_\.]*))',
        remainder
    )

    # Make each part lowercase, unless it's an acronym
    subnames_case_corrected = []

    for sm in subname_matches:

        if re.match('[A-Z]{2,}[^A-Z_\.]*', sm[0]):
            subnames_case_corrected.append(sm[0])
        else:
            subnames_case_corrected.append(sm[0].lower())

    return ' '.join([subname0] + subnames_case_corrected)

for name, val in value_names_database.items():
    print(name, '-->', clean_molly_varname(name))