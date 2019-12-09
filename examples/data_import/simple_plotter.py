'''
Example script for plotting QNCMBE data.

You must first install the qncmbe python module (see README).
Also, your computer must have access to the server \\insitu1.nexus.uwaterloo.ca
'''

import datetime as dt
from qncmbe.data_import.data_import_utils import get_data
from qncmbe.data_import.value_names import value_names_database
import matplotlib.pyplot as plt


def main():

	# Start time. datetime() is a function from the datetime package, and its arguments are (year, month, day, hour, minute, second)
	start_time = dt.datetime(2019,9,24,17,30,0)

    # End time. Something like "start_time + dt.timedelta(hours = 24)" will set the end time to 24 hours after the start time.
	end_time = start_time + dt.timedelta(hours = 3)

	# x value for the plot. Usually "Molly time", but could also be, e.g., "BET time". 
	# For full options, refer to Value_names_database.csv
	# or call qncmbe.data_import.value_names.print_allowed_value_names()
	x_value = "Molly time"

	# list of y values for the plot.

	y_values = ["Al1 base measured"]
	#y_values = ["Ga2 tip setpoint"]

	simple_plot(start_time, end_time, x_value, y_values)

	plt.show()

def simple_plot(start_time, end_time, x_value, y_values):

	import_values = [x_value] + y_values

	delta_t = 2.0
	data = get_data(start_time, end_time, import_values, delta_t, interp = True)

	fig, ax = plt.subplots()

	for y_value in y_values:
		y_units = value_names_database[y_value]['Units']
		ax.plot(data[x_value], data[y_value], label = f"{y_value} ({y_units})")

	ax.set_title("MBE data plot")

	x_units = value_names_database[x_value]['Units']
	ax.set_xlabel(f"{x_value} ({x_units})")

	ax.legend()

	return fig, ax

if __name__ == "__main__":
	main()
