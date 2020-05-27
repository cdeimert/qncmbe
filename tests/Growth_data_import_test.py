import os
import logging

import matplotlib.pyplot as plt

from qncmbe.data_import.growths import GrowthDataCollector
from qncmbe.data_import.utils import console_handler
import qncmbe.plotting as pltutils


pltutils.load_plot_style('qncmbe', update_style_files=False)

verbose = False

if verbose:
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s (%(name)s): %(message)s')
    )

this_dir = os.path.dirname(os.path.abspath(__file__))

save_dir = os.path.join(this_dir, 'data_saves')

data_dirs = {
    "BET": os.path.join(this_dir, 'example_data'),
    "SVT": os.path.join(this_dir, 'example_data', 'SVT Data'),
    "Molly": os.path.join(this_dir, 'example_data', 'Molly Data')
}

names = [
    'BET temp',
    'Refl calib 950',
    'GM1 subs center measured',
    'GaTe1 tip working setpoint'
]

collector = GrowthDataCollector(
    start_time="2019-12-22 12:00",
    end_time="2019-12-24 14:00",
    names=names,
    savedir=save_dir,
    molly_dt=None
)

collector._set_test_mode()

for location, path in data_dirs.items():
    collector.set_data_path(location, path)

data = collector.get_data(force_reload=True)

for name in names:
    fig, ax = plt.subplots()
    data[name].plot(fig, ax)

plt.show()
