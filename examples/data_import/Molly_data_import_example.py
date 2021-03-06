import os

import matplotlib.pyplot as plt

from qncmbe.data_import.molly import MollyDataCollector
from qncmbe.plotting import styles

styles.use('qncmbe')

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
    savedir=save_dir,
    dt=None
)

collector.main_data_path = data_dir

data = collector.get_data(force_reload=True)

fig, ax = plt.subplots()
for name in names:
    data[name].plot(fig, ax, marker='.')

print(data['Al1 base setpoint'][:8].time)

plt.show()
