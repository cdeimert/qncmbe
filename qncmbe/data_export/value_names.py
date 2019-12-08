from collections import OrderedDict
import csv
import os.path as path

thisdir = path.dirname(path.abspath(__file__))
database_file = path.join(thisdir, 'value_names_database.csv')

reader = csv.DictReader(open(database_file, 'rt'))

value_names_database = OrderedDict()

for line in reader:
    value_names_database[line['Value name']] = {
            'Location': line['Location'],
            'Local value name': line['Local value name'],
            'Measurement type': line['Measurement type'],
            'Units': line['Units']
        }

def print_allowed_value_names(full_csv = False):

    if full_csv:
        headers = ['Value name', 'Location', 'Local value name', 'Measurement type', 'Units']
        out_str = ','.join(headers)
    else:
        out_str = ''

    for vn in value_names_database:
        out_str += vn 

        if full_csv:
            for header in headers[1:]:
                out_str += ',' + value_names_database[vn][header]
    
        out_str += '\n'
    
    print(out_str)

    return out_str


def get_value_names_list(location = "all"):
	'''
    Gets a list of all value names from the value names database if location == "all"
	Otherwise, only returns value names from a particular location (either "Molly", "SVT", or "BET")
    '''

	value_names_list = []
	for val in value_names_database:
		if (location == "all") or (location == value_names_database[val]["Location"]):
			value_names_list.append(val)

	return value_names_list