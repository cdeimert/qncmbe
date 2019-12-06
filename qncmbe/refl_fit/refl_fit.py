'''
Functions for fitting reflectance oscillations in Molecular Beam Epitaxy growths.
Based on the method of Breiland et al ("A virtual interface method for extracting growth rates and high temperature optical constants from thin semiconductor films using in situ normal incidence reflectance", Journal of Applied Physics, 1995)

TODO: 
  - Refactor to get rid of the fittable parameter weirdness... 
    Should just pass a list of parameters to be fitted.
  - Add the ability to plot fit convergence over time. (Part done, but would be better if you could pick a specific parameter.)
'''

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
import scipy.signal as sig

wvln_colors_light = {
    '469.5': '#80b1d3',
    '950.3': '#fb8072'
}
wvln_colors_dark = {
    '469.5': '#377eb8',
    '950.3': '#e41a1c'
}

refl_pars = ['n','k','ns','ks','G','s','wlvn']

class Material():
    def __init__(self, name):
        self.name = name
        self.N = {}
        
    def set_N_at_wavelength(self, wavelength, N):
        self.N[wavelength] = N

class Fittable_parameter():
    def __init__(self, value, is_fitted = False):
        self.value = value
        self.is_fitted = is_fitted
                
class Refl_parameters():
    def __init__(self, N, Ns, G, s, wvln):
        self.N = Fittable_parameter(N)
        self.Ns = Fittable_parameter(Ns)
        self.G = Fittable_parameter(G)
        self.s = Fittable_parameter(s)
        self.wvln = Fittable_parameter(wvln)
           
    def set_fit_type(self, fit_type):
        '''
        Valid fit types:
        - "fix nk" (fit everything else, except wavelength)
        - "fix G" (fit everything else, except wavelength)
        - "fit everything" (fit everything except wavelength)
        '''
        
        self.N.is_fitted = True
        self.Ns.is_fitted = True
        self.G.is_fitted = True
        self.s.is_fitted = True
        self.wvln.is_fitted = False
        
        if fit_type == "fix nk":
            self.N.is_fitted = False
        elif fit_type == "fix G":
            self.G.is_fitted = False
        elif fit_type == "fit everything":
            pass
        else:
            print("Invalid fit selection, fitting everything except wavelength.")
            
    def copy(self):
        new_refl_pars = Refl_parameters(self.N.value, self.Ns.value, self.G.value, self.s.value, self.wvln.value)
        
        new_refl_pars.N.is_fitted = self.N.is_fitted
        new_refl_pars.Ns.is_fitted = self.Ns.is_fitted
        new_refl_pars.G.is_fitted = self.G.is_fitted
        new_refl_pars.s.is_fitted = self.s.is_fitted
        new_refl_pars.wvln.is_fitted = self.wvln.is_fitted
        
        return new_refl_pars

def calc_reflectance(time, n, k, ns, ks, G, s, wvln):
        
    N = n - 1j*k
    Ns = ns - 1j*ks

    r_inf = (1 - N)/(1 + N)
    r_i = (N - Ns)/(N + Ns)

    exp_factor = r_i*np.exp(-1j*4.0*np.pi*N*G*time/wvln)

    r = (r_inf + exp_factor)/(1 + r_inf*exp_factor)

    return s*np.absolute(r)**2

def dict_to_list(in_dict, keys):
	return [in_dict[key] for key in keys]

def list_to_dict(in_list, keys):
	return {k:v for k,v in zip(keys, in_list)}

# def fit_reflectance_new(refl, time, pars_guess, pars_to_fit):
#     '''
#     - refl and time should be numpy arrays with the reflectancs vs time data
#     - pars_guess should be a dictionary with keys equal to {'n', 'k', 'ns', 'ks', 'G', 's', 'wvln'}
#     - pars_to_fit should be a comma-separated string. E.g., 'ns,ks,G,s' or 'n,k,s'
#     '''

#     pfit_keys = pars_to_fit.split(',')

#     if not set(pfit_keys).issubset(set(refl_pars)):
#         raise Exception(f"Invalid pars_to_fit. Must be subset of {','.join(refl_pars)}")

#     pfix = {}
#     for p in refl_pars:
#         if p not in pfit_keys:
#             pfix[p] = pars_guess[p]

#     pfit = {pars_guess[p] for p in pfit_keys}

#     refl_func = lambda t, *p_arr: calc_reflectance(t, **{k: p for k, p in zip(pfit_keys, p_arr)}, **pfix)

#     p0 = [pars_guess[p] for p in pars_to_fit]

#     rel_time = time - time[0]

#     try:
#         popt, pcov = opt.curve_fit(refl_func, rel_time, refl, p0 = p0)
#     except:
#         pars_opt = pars_guess
#         refl_fit = refl_func(rel_time, *p0, **pfix)
#         print("WARNING: fit failed.")
#         return pars_opt, refl_fit

#     pars_opt = {**pfix, k:p for k,p in zip(pfit_keys, popt)}

#     refl_fit = refl_func(rel_time, *popt, **pfix)

#     return pars_opt, refl_fit

def fit_reflectance(refl, time, refl_pars_guess):
    # 'reflectance' and 'time' should be 1D numpy arrays of the same length
    # refl_pars should be of class Refl_parameters
    
    par_keys = np.array(['n', 'k', 'ns', 'ks', 'G', 's', 'wvln'])
    
    par_guess = {
        'n': np.real(refl_pars_guess.N.value),
        'k': -np.imag(refl_pars_guess.N.value),
        'ns': np.real(refl_pars_guess.Ns.value),
        'ks': -np.imag(refl_pars_guess.Ns.value),
        'G': refl_pars_guess.G.value,
        's': refl_pars_guess.s.value,
        'wvln': refl_pars_guess.wvln.value
    }
    
    par_is_fitted = {
        'n': refl_pars_guess.N.is_fitted,
        'k': refl_pars_guess.N.is_fitted,
        'ns': refl_pars_guess.Ns.is_fitted,
        'ks': refl_pars_guess.Ns.is_fitted,
        'G': refl_pars_guess.G.is_fitted,
        's': refl_pars_guess.s.is_fitted,
        'wvln': refl_pars_guess.wvln.is_fitted
    }
       
    p_fit = np.array(dict_to_list(par_is_fitted, par_keys)) # List version of parameters to fit
    p_fix = np.logical_not(p_fit) # List version of parameters to fix

    fixed_vals = {key: par_guess[key] for key in par_keys[p_fix]}

    refl_func = lambda t, *p: calc_reflectance(t, **{key: p_val for key, p_val in zip(par_keys[p_fit], p)}, **fixed_vals)

    p0 = dict_to_list(par_guess, par_keys[p_fit])

    rel_time = time - time[0]

    try:
        p_opt, p_cov = opt.curve_fit(refl_func, rel_time, refl, p0 = p0)
    except:
        refl_pars_fit = refl_pars_guess.copy()
        refl_fit = calc_reflectance(rel_time, **par_guess)
        print("WARNING: fit failed.")
        return refl_pars_fit, refl_fit

    par_opt = list_to_dict(p_opt, par_keys[p_fit])
    
    for key in par_keys[p_fix]:
        par_opt[key] = par_guess[key]
  
    refl_pars_fit = refl_pars_guess.copy()

    refl_pars_fit.N.value = par_opt['n'] - 1j*par_opt['k']
    refl_pars_fit.Ns.value = par_opt['ns'] - 1j*par_opt['ks']
    refl_pars_fit.G.value = par_opt['G']
    refl_pars_fit.s.value = par_opt['s']
    refl_pars_fit.wvln.value = par_opt['wvln']
    
    refl_fit = calc_reflectance(rel_time, **par_opt)

    return refl_pars_fit, refl_fit


def print_fitted_value(name, x_fit, x_guess, units = '', print_error = True):
    
    if units != '':
        pad_units = ' ' + units
    else:
        pad_units = ''

    if x_fit.is_fitted:
    
        if (np.abs(x_guess.value) > 1e-20) and print_error:
            x_err = (x_fit.value - x_guess.value)*100/x_guess.value
            string = '{} = {:.5f}{} ({:.5f} % away from initial guess of {:.5f}{})'.format(name, x_fit.value, pad_units, x_err, x_guess.value, pad_units)
        else:
            string = '{} = {:.5f}{} (Initial guess: {:.5f}{})'.format(name, x_fit.value, pad_units, x_guess.value, pad_units)
        
    else:
        string = '{} = {:.5f}{} (Fixed)'.format(name, x_fit.value, pad_units)
        
    return string + '\n'

class Layer():
    def __init__(self, material, growth_rate, t_start = -np.inf, t_end = np.inf):
        '''
        - material should be of class Material
        - growth_rate should be a float (if using angtroms, should call use_angstroms_for_structure())
        - If t_start and t_end are specified, will automatically use them to restrict the data provided in set_refl_data()
        '''
        self.material = material
        self.material_beneath = None
        self.G = growth_rate

        self.t_start = t_start
        self.t_end = t_end

        self.name = ''

        self.wvln_scale = 1.0
        self.use_angstroms = False
                
    def set_name(self, name):
        self.name = name
        
    def set_material_beneath(self, material):
        self.material_beneath = material                       
    
    def set_refl_data(self, t, R):
        '''
        t should be a numpy array of time values
        R should be a dictionary of numpy arrays. One entry for each wavelength.
        '''

        mask = (t >= self.t_start) & (t <= self.t_end)
        
        self.t_data = t[mask]
        self.refl_data = {key: R[key][mask] for key in R}
    
    def use_angstroms_for_structure(self, use_angstroms = True):
        self.use_angstroms = use_angstroms

        if use_angstroms:
            self.wvln_scale = 10.0
        else:
            self.wvln_scale = 1.0

    def set_refl_pars_guess(self, fit_type = 'fix nk'):
        
        self.refl_pars_guess = {}
        
        for wvln in self.refl_data:

            if self.material_beneath is not None:
                Ns_guess = self.material_beneath.N[wvln]
            else:
                Ns_guess = 1.0 + 0j

            self.refl_pars_guess[wvln] = Refl_parameters(self.material.N[wvln], 
                                                         Ns_guess,
                                                         self.G, 
                                                         1.0, 
                                                         float(wvln)*self.wvln_scale)
            
        self.set_fit_type(fit_type)
            
    def set_fit_type(self, fit_type):
        
        for wvln in self.refl_data:
            self.refl_pars_guess[wvln].set_fit_type(fit_type)
    
    def calc_refl_fit(self):
        
        self.refl_pars_fit = {}
        self.refl_fit = {}
        
        for wvln in self.refl_data:
            self.refl_pars_fit[wvln], self.refl_fit[wvln] = fit_reflectance(self.refl_data[wvln],
                                                                            self.t_data,
                                                                            self.refl_pars_guess[wvln])
        
    def print_refl_fit(self):
        
        string = '------------------------------\n'
        string += 'Layer: {}\n'.format(self.name)

        for wvln in self.refl_fit:
            
            pars_fit = self.refl_pars_fit[wvln]
            pars_guess = self.refl_pars_guess[wvln]
            
            string += '\nWavelength = {} nm'.format(wvln)
            string += '\n'
            string += print_fitted_value('N', pars_fit.N, pars_guess.N, print_error = False)
            string += print_fitted_value('Ns', pars_fit.Ns, pars_guess.Ns, print_error = False)

            if self.use_angstroms:
                G_units = 'Å/s'
            else:
                G_units = 'nm/s'
            string += print_fitted_value('G', pars_fit.G, pars_guess.G, units = G_units)
            string += print_fitted_value('s', pars_fit.s, pars_guess.s, print_error = False)
            
        string += '------------------------------\n'

        return string

    def print_growth_rate_summary(self):

        string = '------------------------------\n'
        string += 'Layer: {}\n'.format(self.name)

        for wvln in self.refl_fit:
            
            pars_fit = self.refl_pars_fit[wvln]
            pars_guess = self.refl_pars_guess[wvln]
            
            string += 'Wavelength = {} nm\n'.format(wvln)
            if self.use_angstroms:
                G_units = 'Å/s'
            else:
                G_units = 'nm/s'
            string += print_fitted_value('G', pars_fit.G, pars_guess.G, units = G_units)
        
        string += '------------------------------\n'

        return string    
    
    
    def plot_refl_fit(self):
        
        fig, ax = plt.subplots()
        
        n = 0
        for wvln in self.refl_data:
            if wvln in wvln_colors_light:
                color = wvln_colors_light[wvln]
            else:
                color = f'C{n}'
                n+=1
            ax.plot(self.t_data, self.refl_data[wvln], '-', label = wvln + " nm data", color = color)
            ax.plot(self.t_data, self.refl_fit[wvln], ':k', label = wvln + " nm fit")
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Refl.')
        ax.legend()
        
        ax.set_title(self.name)

        return fig, ax
        
        
class Structure():
    def __init__(self, substrate):
        # Substrate should be of class Material
        
        self.substrate = substrate
        self.layers = []
        self.layer_names = []
        self.use_angstroms = False
        self.fit_type = 'fix nk'

        self.use_data_file = False
        
    def set_refl_data(self, t_data, R_data):
        self.t_data = t_data
        self.R_data = R_data

    def set_refl_data_file(self, fname):
        self.refl_data_file = fname
        self.use_data_file = True

        self.update_refl_data()

    def update_refl_data(self):
        
        if self.use_data_file:
            raw_data = np.genfromtxt(self.refl_data_file, skip_header = 3, usecols = (0,1,2))

            self.t_data = raw_data[:,0]*3600*24
            self.R_data = {
                '950.3': raw_data[:,1],
                '469.5': raw_data[:,2]
                }
            self.t_data -= self.t_data[0]

        else:
            pass

    def plot_full_refl_data(self):
        
        self.update_refl_data()

        fig, ax = plt.subplots()
        
        n = 0
        for wvln in self.R_data:
            if wvln in wvln_colors_dark:
                color = wvln_colors_dark[wvln]
            else:
                color = f'C{n}'
                n+=1
            ax.plot(self.t_data, self.R_data[wvln], '-', label = wvln + " nm", color = color)
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Refl.')
        ax.legend()

        title = 'Full reflectane data'
        if self.use_data_file:
            title += f' ("{self.refl_data_file}")'
        ax.set_title(title)

        return fig, ax

    def get_full_refl_data(self):
        self.update_refl_data()
        return self.t_data, self.R_data

    def use_angstroms_for_structure(self, use_angstroms = True):
        self.use_angstroms = use_angstroms
        for layer in self.layers:
            layer.use_angstroms_for_structure(use_angstroms)
            layer.set_refl_pars_guess(self.fit_type)

    def add_layer(self, name, material, growth_rate, t_start, t_end, use_layer_beneath = False):
        
        new_layer = Layer(material, growth_rate, t_start, t_end)

        if name in self.layer_names:
            raise Exception(f'Layer name "{name}" already used. Each layer must have a unique name.')
        
        new_layer.set_name(name)
        
        # If possible & requested, use the previous layer to generate an initial guess for the substrate dielectric constant
        if use_layer_beneath:
            if self.layers:
                new_layer.set_material_beneath(self.layers[-1].material)  
            else:
                new_layer.set_material_beneath(self.substrate)  
        
        new_layer.set_refl_data(self.t_data, self.R_data)
        new_layer.use_angstroms_for_structure(self.use_angstroms)
        new_layer.set_refl_pars_guess()
        
        self.layers.append(new_layer)
        self.layer_names.append(name)
        
    def set_fit_type(self, fit_type):
        for layer in self.layers:
            layer.set_fit_type(fit_type)

        self.fit_type = fit_type

    def calc_refl_fits(self):

        self.update_refl_data()

        for layer in self.layers:
            layer.set_refl_data(self.t_data, self.R_data)
            layer.calc_refl_fit()
            
    def display_fit_results(self):
        for layer in self.layers:
            layer.plot_refl_fit()
            print(layer.print_refl_fit())

    def print_growth_rate_summary(self):
        for layer in self.layers:
            print(layer.print_growth_rate_summary())
    
    def get_layer_by_name(self, name):
        for layer in self.layers:
            if layer.name == name:
                return layer

    def get_fit_convergence(self, layer_name, t_buffer, t_step):
        layer = self.get_layer_by_name(layer_name)

        self.update_refl_data()

        t_out = []
        p_out = []
        
        t_start = layer.t_start
        t_end = layer.t_end

        t = t_start + t_buffer

        while (t <= t_end) and (t <= self.t_data[-1]):
            layer.t_end = t
            layer.set_refl_data(self.t_data, self.R_data)
            layer.calc_refl_fit()

            t_out.append(t)
            p_out.append(layer.refl_pars_fit)

            t += t_step
        layer.t_end = t_end
        layer.set_refl_data(self.t_data, self.R_data)
        layer.calc_refl_fit()

        return t_out, p_out

