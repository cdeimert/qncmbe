import qncmbe.data_import.data_import_utils as imp
from qncmbe.plotting import plt
import datetime as dt

start_time = dt.datetime(2019, 10, 4, 16, 50, 0)
end_time = dt.datetime(2019, 10, 5, 16, 50, 0)

data = imp.get_SVT_data(start_time, end_time, ['SVT Time (RoboMBE IS4K Refl)', 'Calib 950'])

fig, ax = plt.subplots()
ax.plot(data['SVT Time (RoboMBE IS4K Refl)'], data['Calib 950'])
plt.show()
