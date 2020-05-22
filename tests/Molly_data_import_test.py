import os

import matplotlib.pyplot as plt

from qncmbe.data_import.molly import MollyDataCollector
import qncmbe.plotting as pltutils

pltutils.load_plot_style('qncmbe', update_style_files=False)

this_dir = os.path.dirname(os.path.abspath(__file__))

save_dir = os.path.join(this_dir, 'data_saves')

data_dir = os.path.join(this_dir, 'example_data', 'Molly Data')

names = [
    'Al1 base measured',
    'Al1 base setpoint',
    'Al1 base working setpoint',
]

collector = MollyDataCollector(
    start_time="2019-09-24 08:00",
    end_time="2019-09-25 00:00",
    names=names,
    savedir=save_dir
)

collector.main_data_path = data_dir

data = collector.get_data(force_reload=True)

fig, ax = plt.subplots()
for name in names:
    data[name].plot(fig, ax, marker='.')

plt.show()
