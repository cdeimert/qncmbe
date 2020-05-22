import os

import matplotlib.pyplot as plt

from qncmbe.data_import.BET import BETDataCollector
import qncmbe.plotting as pltutils

pltutils.load_plot_style('qncmbe', update_style_files=False)

this_dir = os.path.dirname(os.path.abspath(__file__))

save_dir = os.path.join(this_dir, 'data_saves')

data_dir = os.path.join(this_dir, 'example_data')

names = [
    'BET_temp',
    'ISP_temp'
]

collector = BETDataCollector(
    start_time="2019-12-22 12:00",
    end_time="2019-12-24 14:00",
    names=names,
    savedir=save_dir
)

collector.main_data_path = data_dir

data = collector.get_data()

fig, ax = plt.subplots()
for name in names:
    data[name].plot(fig, ax)

plt.show()
