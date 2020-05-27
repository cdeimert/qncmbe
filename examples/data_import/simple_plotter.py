'''
Example script for plotting QNCMBE data.

You must first install the qncmbe python module (see README).
Also, your computer must have access to
\\insitu1.nexus.uwaterloo.ca and \\zw-xp1
'''

# Load packages
from qncmbe.data_import.core import get_growth_data, print_names_list
import matplotlib.pyplot as plt

from qncmbe.plotting import load_plot_style

load_plot_style('qncmbe', update_style_files=False)

# Uncomment this line to print a list of allowed data names
# print_names_list(); exit()

# Set start and end times
start_time = "2019-09-24 17:30"
end_time = "2019-09-24 20:30"

# Pick which data values to plot
names = [
    "Al1 base measured",
    "Al1 tip measured"
]

# Collect data
data = get_growth_data(start_time, end_time, names)

# Plot
fig, ax = plt.subplots()

for name in names:
    data[name].plot(fig, ax)

plt.show()
