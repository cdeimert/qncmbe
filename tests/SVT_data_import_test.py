import os

import matplotlib.pyplot as plt

from qncmbe.data_import.data_import_utils import SVTDataCollector
import qncmbe.plotting as pltutils

pltutils.load_plot_style('qncmbe', update_style_files=False)

thisdir = os.path.dirname(os.path.abspath(__file__))

savedir = os.path.join(thisdir, 'data_saves')

names = [
    'refl_calib_950',
    'refl_calib_470'
]

collector = SVTDataCollector(
    start_time="2019-10-04 00:00",
    end_time="2019-10-05 12:00",
    names=names,
    savedir=savedir
)

data = collector.get_data(force_reload=True)

fig, ax = plt.subplots()
for name in names:
    data[name].plot(fig, ax, marker='')

plt.show()
