from qncmbe.refl_fit.refl_fit import Material, Structure, plt
import numpy as np

import os

GaAs = Material('GaAs')
AlAs = Material('AlAs')

# Refractive indices fitted to XRD
GaAs.set_N_at_wavelength('950.3', 3.7575 - 0.1070j)
GaAs.set_N_at_wavelength('469.5', 4.667 - 1.594j)

AlAs.set_N_at_wavelength('950.3', 3.047 - 0.00j)
AlAs.set_N_at_wavelength('469.5', 3.7341 - 0.1022j)

#growth = 'G0641'
#filepath = f'\\\\insitu1.nexus.uwaterloo.ca\\QNC_MBE_Data\\ZW-XP1\\{growth}\\{growth}_IS4K Refl.txt'

filepath = 'examples\\refl_fit\\G0641_IS4K Refl.txt'

struct = Structure(substrate = GaAs)

struct.set_refl_data_file(filepath)

struct.plot_full_refl_data()

struct.use_angstroms_for_structure() #Use angstroms for structure but nm for wavelength

# Add layers to be fitted
struct.add_layer(
    name = 'GaAs-a', 
    material = GaAs, 
    growth_rate = 1.8, 
    t_start = 2303, 
    t_end = 4214)

struct.add_layer(
    name = 'AlAs', 
    material = AlAs, 
    growth_rate = 0.4513, 
    t_start = 5504, 
    t_end = 10542)

struct.add_layer(
    name = 'GaAs-b', 
    material = GaAs, 
    growth_rate = 1.8, 
    t_start = 11479, 
    t_end = 13195)


# Fits with n,k fixed
struct.set_fit_type('fix nk')

struct.calc_refl_fits()
struct.display_fit_results()

struct.print_growth_rate_summary()

t, p_arr = struct.get_fit_convergence('GaAs-b', 300, 50)

fig, ax = plt.subplots()
ax.plot(t, [p['950.3'].G.value for p in p_arr])

plt.show()
