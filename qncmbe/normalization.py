'''
This module is for normalizing units. 
We measure length in nm, energy in meV, and choose the remaining units so that the following are all equal to 1:
	q0 (electron charge)
	hbar (reduced Planck constant)
	kB (Boltzmann constant)

---------- Usage ----------

Typically the process is as follows:
1. Normalize input values
2. Do calculations in normalized units
3. Denormalize to display output

Use the normalize() function to put a quantity into normalized units.
E.g., normalize(300.0, 'K') will return ~25.85, since temperature is essentially measured in meV.

After doing calculations in normalized units, use the denormalize() function to return.
E.g., denormalize(25.85, 'K') will return ~300. This is putting the normalized temperature 25.85 back into Kelvin.

Note that unit strings can be more complex, such as 'kg.m^2.s^-2'.
They should always be of the form 'u1^p1.u2^p2.u3^p3...' 
The powers p1, p2, p3... can be floats such as 'm^0.5', or fractions such as 'm^1/2', or they can be skipped entirely, such as 'cm'.

The following SI prefixes can be used:
P, T, G, M, k, c, m, u, n, p, f
with the following units:
m, s, g, K, Hz, F, C, eV, J

Some useful constants are also defined, in normalized units:
	c0 = Speed of light in vacuum
	eps0 = Permittivity of free space
	m_el = Electron mass
	kB = Boltzmann's constant
	hbar = Reduced Planck constant
	q0 = Electron charge

---------- Explanation ----------
Values are normalized relative to the following quantities:
    Length: 			L0 = 1.0 nm
    Energy:	 			E0 = 1 meV = 1.60217662e-22 J
    Electron charge:	q0 = 1.60217662e-19 C
    Planck const.: 		hbar = 6.582119514e-16 eV.s.rad^-1
    Boltzmann const.:	kB = 8.6173303e-5 eV.K^-1

The idea is that, for example, a length L can be written as L = l*L0, where l is dimensionless.

From these, we can derive normalization constants for other dimensions, such as:
	Angular frequency:	w0 = E0/hbar
	Time: 				t0 = 1/f0 = hbar/E0
	Speed:				v0 = L0/t0 = L0*E0/hbar
	Mass:				m0 = E0/v0^2 = hbar^2/(L0^2*E0)
	Capacitance:		C0 = q0^2/E0
	Temperature:		T0 = E0/kB

Then we can use these to derive normalized formulas.
For example, we have an oscillator strength given by
	f = 2*m*w*z^2/hbar
Now we replace:
	f --> f (dimensionless)
	m --> m*m0 = m*hbar^2/(L0^2*E0) (mass)
	w --> w*w0 = w*E0/hbar (angular frequency)
	hbar --> 1*hbar
	z --> z*L0
After replacement, these all become dimensionless quantities, multiplied by unit-ed scaling factors.
Replacing in the formula, we get
	f = 2*m*(hbar^2/(L0^2*E0))*w*(E0/hbar)*z^2*L0^2/hbar
After simplifying, the normalized formula is
	f = 2*m*w*z^2
Notice that the hbar has dropped out of the formula!

This amount of work does not need to be done generally. If the equation is dimensionally consistent, all the scaling factors will cancel out. To obtain the normalized formulas, simply set hbar, q0, kB --> 1.
'''

# Non-standard library imports (included in setup.py)
from numpy import pi

def parse_units_string(string):
    '''
	Input string should be unit string of the form "u1^p1.u2^p2.u3^p3..."
    
	This function converts that into a list with unit-power pairs
    
    Examples:
    'cm' --> [['cm', 1]]
    'cm^2' --> [['cm', 2]]
    'kg.m^2.s^-2' --> [['kg',1], ['m',2], ['s',-2]]
    'm^0.5' --> [['m',0.5]]
    'm^1/2' --> [['m',0.5]]
    '''
    
    units = string.split('.')

    for i, unit in enumerate(units):
        units[i] = unit.split('^')
        if len(units[i]) == 1:
            units[i].append('1')
    
    for i,[u,p] in enumerate(units):
        if '/' in p:
            num, den = p.split('/')
            units[i][1] = float(num)/float(den)
        else:
            units[i][1] = float(p)
            
    return units

def normalize(val, unit):

	units_list = parse_units_string(unit)

	out_val = val*1.0
	for u,p in units_list:
		out_val /= norm[u]**p

	return out_val

def denormalize(val, unit):

	units_list = parse_units_string(unit)

	out_val = val*1.0
	for u,p in units_list:
		out_val *= norm[u]**p

	return out_val

def convert_units(val, unit_in, unit_out):
	norm_val = normalize(val, unit_in)
	out_val = denormalize(norm_val, unit_out)

	return out_val

# This is the value of the 'normalizing' quantity, in the specified units.
norm = {
	# Length
	'm': 1e-9,
	'angstrom': 10.0,
	# Energy
	'J': 1.60217662e-22,
	'eV': 0.001,
	'meV': 1.0,
	# Angular momentum
	'J.s.rad^-1': 1.054571800e-34,
	'eV.s.rad^-1': 6.582119514e-16,
	'hbar': 1.0,
	# Charge
	'C': 1.60217662e-19,
	'q0': 1.0,
	# Boltzmann constant
	'eV.K^-1': 8.6173303e-5,
	'J.K^-1': 1.38064852e-23,
	'kB': 1.0
}

norm['rad'] = 1.0

# Angular frequency
norm['rad.s^-1'] = norm['eV']/norm['eV.s.rad^-1']

# Frequency
norm['Hz'] = norm['rad.s^-1']

# Time
norm['s'] = 1/norm['Hz']

# Temperature
norm['K'] = norm['eV']/norm['eV.K^-1']

# Speed
norm['m.s^-1'] = norm['m']/norm['s']

# Mass
norm['kg'] = norm['J']/(norm['m.s^-1']**2)
norm['g'] = norm['kg']*10**3

# Capacitance
norm['F'] = (norm['C']**2)/norm['J']

# SI prefixes
SI_prefix = {'P': 15, 'T': 12, 'G': 9, 'M': 6, 'k': 3,
			 'c': -2, 'm': -3, 'u': -6, 'n': -9, 'p': -12, 'f': -15}

# SI units
SI_units = ['m', 's', 'g', 'K', 'Hz', 'F', 'C', 'eV', 'J']

for u in SI_units:
	for pf in SI_prefix:
		norm[pf+u] = norm[u]*10**(-SI_prefix[pf])

c0 = normalize(299792458,'m.s^-1')
eps0 = normalize(8.854187817e-12, 'F.m^-1')
m_el = normalize(9.10938356e-31, 'kg')
kB = normalize(8.6173303e-5, 'eV.K^-1')
hbar = normalize(6.582119514e-16, 'eV.s.rad^-1')
q0 = normalize(1.60217662e-19, 'C')

norm['c0'] = c0
norm['eps0'] = eps0
norm['m_el'] = m_el