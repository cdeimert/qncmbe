'''
Example file for the reflectance fitting module qncmbe.refl_fit

Based on the data from QNC-MBE growth G0641, which is included ('G0641_IS4K Refl.txt')
'''
from qncmbe.refl_fit import Material, Structure, plt
import numpy as np

import os

### Set up materials
GaAs = Material('GaAs')
AlAs = Material('AlAs')

GaAs.set_nk_at_wavelength('950.3', n=3.7575, k=0.1070)
GaAs.set_nk_at_wavelength('469.5', n=4.667,  k=1.594)

AlAs.set_nk_at_wavelength('950.3', n=3.047,  k=0.00)
AlAs.set_nk_at_wavelength('469.5', n=3.7341, k=0.1022)

### Set file of reflectance data

# Path to the datafile. Might need to adjust this depending how you run your python code.
filepath = 'examples\\refl_fit\\G0641_IS4K Refl.txt'

# If your computer has access to \\insitu1.nexus.uwaterloo.ca
# use the following to pull real-time reflectance data directly from the ZW-XP1 computer
#
# growth = 'G0641'
# filepath = f'\\\\insitu1.nexus.uwaterloo.ca\\QNC_MBE_Data\\ZW-XP1\\{growth}\\{growth}_IS4K Refl.txt'

### Set up Structure class.
# This class stores all the reflectance data, and info about the layers grown
# It includes functions for fitting reflectance oscillations and plotting
struct = Structure()

# Set the datafile
# You can alternatively set the data directly using set_refl_data
# However, this way is useful if you're in the middle of a growth and the data file is always being updated
# Using a file link ensures that whenever you call functions to calculate fits later, it will use the most up-to-date data 
struct.set_refl_data_file(filepath)

# Plot the full set of data from the file.
# You will need to look at this to set the time range for each layer to be fit
struct.plot_full_refl_data()

# Use angstroms for structure (i.e. growth rate) but nm for wavelength
struct.use_angstroms_for_structure()

# Add layers to be fitted
# Need to tell it the material, material_beneath, growth rate, and where it lies in the reflectance data
# Note1: if "t_end" is beyond the end of the data, it will just use up to the end of the data
# Note2: material_beneath is just used to set the initial guess of the ns, ks in the fit. Can be set to "None", but fit is less likely to succeed.
struct.add_layer(
    name = 'GaAs-a', 
    material = GaAs, 
    material_beneath = AlAs,
    growth_rate = 1.8, # Å/s
    t_start = 2303,
    t_end = 4214)

struct.add_layer(
    name = 'AlAs', 
    material = AlAs, 
    material_beneath = GaAs,
    growth_rate = 0.4513, # Å/s
    t_start = 5504, 
    t_end = 10542)

struct.add_layer(
    name = 'GaAs-b', 
    material = GaAs, 
    material_beneath = AlAs,
    growth_rate = 1.8, # Å/s
    t_start = 11479, 
    t_end = 13195)


# Define which parameters to fit via a comma-separated list (no spaces).
# Valid options are 'n', 'k', 'ns', 'ks', 'G', 's', and 'wvln'
struct.set_pars_to_fit('ns,ks,G,s')

# Calculate the reflectance fits and display the results
# It will generate plots and also print out the fit results.
struct.calc_refl_fits()
struct.display_fit_results()

# Print a summary of all the fit results (just the growth rates)
struct.print_growth_rate_summary()

# Plot the convergence of the fit vs time for one of the layers
# This will fit from the start of the layer (t0) up to t0 + t_buffer + n*t_step
# It will do a separate fit for n = 0,1,2... until it reaches the end of the layer.
# This way you can see how the fitted value (growth rate, in this case) converges to some final value.
struct.plot_fit_convergence(
    layer_name = 'AlAs', 
    t_buffer = 500, 
    t_step = 50,
    parameter = 'G')

plt.show()
