import os

import matplotlib.pyplot as plt
import numpy as np

from qncmbe.data_import.data_import_utils import MollyDataCollector
import qncmbe.plotting as pltutils

pltutils.load_plot_style('qncmbe', update_style_files=False)

thisdir = os.path.dirname(os.path.abspath(__file__))

savedir = os.path.join(thisdir, 'data_saves')

names = [
    'Al1_base_measured',
    'Al1_base_setpoint',
    'Al1_base_working_setpoint',
]

collector = MollyDataCollector(
    start_time="2019-09-24 08:00",
    end_time="2019-09-25 00:00",
    names=names,
    savedir=savedir
)

data = collector.get_data()

print(data)

#fig, ax = plt.subplots()
#for name in names:
#    data[name].plot(fig, ax)

#plt.show()
