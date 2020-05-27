import os

import matplotlib.pyplot as plt

from qncmbe.data_import.SVT import SVTDataCollector
import qncmbe.plotting as pltutils

pltutils.load_plot_style('qncmbe', update_style_files=False)

this_dir = os.path.dirname(os.path.abspath(__file__))

save_dir = os.path.join(this_dir, 'data_saves')

data_dir = os.path.join(this_dir, 'example_data', 'SVT Data')

names = [
    'Refl calib 950',
    'Refl calib 470'
]

collector = SVTDataCollector(
    start_time="2019-10-04 00:00",
    end_time="2019-10-05 12:00",
    names=names,
    savedir=save_dir
)

collector.main_data_path = data_dir

data = collector.get_data(force_reload=False)

fig, ax = plt.subplots()
for name in names:
    data[name].plot(fig, ax, marker='')

plt.show()
