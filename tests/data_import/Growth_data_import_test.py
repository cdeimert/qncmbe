import os

import matplotlib.pyplot as plt

from qncmbe.data_import.growths import GrowthDataCollector
from qncmbe.plotting import styles

styles.use('qncmbe')

this_dir = os.path.dirname(os.path.abspath(__file__))

save_dir = os.path.join(this_dir, 'data_saves')

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

collector.set_test_mode()

data = collector.get_data(force_reload=True)

for name in names:
    fig, ax = plt.subplots()
    data[name].plot(fig, ax)

plt.show()
