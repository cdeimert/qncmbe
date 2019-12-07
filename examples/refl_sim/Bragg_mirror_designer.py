'''
Simple example of the reflectance oscillation simulator.
In this case, used to design a repeating AlAs/GaAs Bragg mirror on a GaAs substrate.

This uses a simple transfer matrix implementation, from the package qncmbe.refl_sim
'''

from qncmbe.refl_sim import Material, Structure

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Set up materials

GaAs = Material('GaAs')
AlAs = Material('AlAs')

GaAs.set_N_at_wavelength(950.3, 3.7575 - 0.1070j)
AlAs.set_N_at_wavelength(950.3, 3.047 - 0.00j)

GaAs.set_N_at_wavelength(469.5, 4.667 - 1.594j)
AlAs.set_N_at_wavelength(469.5, 3.7341 - 0.1022j)

#### Define structure ####

# Here we define four layers. 
# - The first two (AlAs-a, GaAs-a) are n/2+1/4 wavelengths thick
#   These will give strong reflectance oscillations
# - The next two (AlAs-b, GaAs-b) are n/2 wavelengths thick
#   These will give no reflectance oscillations

wvln = '950.3' # Target wavelength
# Note, for ideal Bragg reflection, the layers should be n/2+1/4 wavelengths thick
# On the other hand, a thickness of n/2 will make the layer invisible.

layers = {
    "AlAs-a": {
        "material": AlAs,
        "num wvlns": 1*0.5,  # Thickness of the layer relative to wvln
        "growth rate": 0.1          # nm/s
    },
    "GaAs-a": {
        "material": GaAs,
        "num wvlns": 2*0.5,
        "growth rate": 0.18
    },
    "AlAs-b": {
        "material": AlAs,
        "num wvlns": 1*0.5 + 0.25,
        "growth rate": 0.1
    },
    "GaAs-b": {
        "material": GaAs,
        "num wvlns": 2*0.5 + 0.25,
        "growth rate": 0.18
    }
}


# Calculate thicknesses
for name in layers:

    nwl = layers[name]["num wvlns"]
    n = layers[name]["material"].N[wvln].real

    layers[name]['thickness'] = nwl*float(wvln)/n

print("Layers:")
for name in layers:
    L = layers[name]['thickness']
    G = layers[name]['growth rate']
    t = L/G
    print(f'{name}: {L:.3f} nm @ {G:.4f} nm/s ({t:.2f} s)')

num_repeats = 2 # Number of times to repeat the sequence of layers

struct = Structure(substrate_material = GaAs)
for i in range(num_repeats):
    for name in layers:
        struct.add_layer(
            material = layers[name]['material'],
            thickness = layers[name]['thickness'],
            growth_rate = layers[name]['growth rate']
        )

#### Calculate reflectance ####
t = {}
R = {}

wavelengths = [950.3, 469.5]

for wl in wavelengths:
    t[str(wl)], R[str(wl)] = struct.calculate_reflectance(wavelength = wl)

#### Plot reflectance ####

fig, ax = plt.subplots()

for layer in struct.layers:
    #tf = layer.t[-1]
    #ax.plot([tf,tf], [0,1], '--k', label = '')
    if layer.material.name == 'AlAs':
        color = (0.7, 0.7, 0.7)
    elif layer.material.name == 'GaAs':
        color = (0.9, 0.9, 0.9)
    rect = patches.Rectangle(([layer.t[0], 0]), layer.t[-1] - layer.t[0], 1.0, facecolor = color, lw = 0.0)
    ax.add_patch(rect)


colors = {'950.3': 'r', '469.5': 'b'}
for wavelength in wavelengths:
    wl = str(wavelength)
    ax.plot(t[wl], R[wl], label = wl + ' nm', color = colors[wl])
    
    
ax.legend()
ax.set_xlabel('Time (s)\n(Dark background: AlAs, Light background: GaAs)')
ax.set_ylabel('Reflectance')
ax.set_ylim([0,1])
ax.set_xlim([0,t[wl][-1]])

plt.tight_layout()
plt.show()
