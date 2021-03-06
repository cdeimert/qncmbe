'''
Example usage of the qncmbe.cell_usage_tracking module

(Below: copied from the cell_usage_tracking.py docstring)
This is a tool for estimating effusion cell usage in the QNC-MBE system

Almost everything is contained in the CellUsageCalculator class. The basic idea
is to pull cell temperature data, as stored by Molly, and to pull A, B, C
calibration coefficients from the Excel document which we manually update.

From this, we can estimate the cell usage as a function of time. There are a
number of uncertainties though. This relies on accurate tracking of the A, B, C
coefficients which may not always be true.

More importantly, when we calculate A,B,C coefficients, we calculate them to
find the flux hitting the centre of the wafer. To calculate the element usage,
though, we need to know the total number of atoms leaving the cell.

For now, we assume that for SUMO cells (Ga, In), 3.5% of the total flux hits
the wafer, while for conical cells (Al) 7% of the total flux hits the wafer.
This was determined approximately in 2017 by comparing the estimated usage to
the actual usage.However, it would be worth doing more accurate measurements
in the future.
'''

import matplotlib.pyplot as plt
import os

from qncmbe.cell_usage_tracking import CellUsageCalculator
from qncmbe.plotting import styles

styles.use('qncmbe')

this_dir = os.path.dirname(os.path.abspath(__file__))

cell_pars_file = 'Z:\\Excell Calculators\\Calibration Parameters V2 2020.xlsx'

ucalc = CellUsageCalculator(
    start_date='2019-05-13',
    end_date='2020-04-30',
    cells='Ga1,Ga2,Al1,In1,In2'.split(','),
    cell_pars_file=cell_pars_file,
    save_dir=os.path.join(this_dir, 'saved_cell_data'),
    delta_t=300,
    force_reload=False  # Note: make sure to force reload if you change delta_t
)

ucalc.calculate_element_usage()

fig, ax = plt.subplots()
ucalc.plot_temperatures(fig, ax)

fig, ax = plt.subplots()
ucalc.plot_mass_usage(fig, ax)

fig, ax = plt.subplots()
ucalc.plot_particle_usage(fig, ax)

ucalc.generate_usage_csv()

ucalc.print_total_usage()

plt.show()
