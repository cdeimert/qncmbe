import os

import matplotlib.pyplot as plt

from qncmbe.data_import.data_import_utils import BETDataCollector
import qncmbe.plotting as pltutils

pltutils.load_plot_style('qncmbe', update_style_files=False)

thisdir = os.path.dirname(os.path.abspath(__file__))

savedir = os.path.join(thisdir, 'data_saves')

names = [
    'BET_temp',
    'ISP_temp'
]

collector = BETDataCollector(
    start_time="2019-12-22 12:00",
    end_time="2019-12-24 14:00",
    names=names,
    savedir=savedir
)

data = collector.get_data()

fig, ax = plt.subplots()
for name in names:
    data[name].plot(fig, ax)

plt.show()
