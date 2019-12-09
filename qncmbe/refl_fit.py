'''
Functions for fitting reflectance oscillations in Molecular Beam Epitaxy growths.
Based on the method of Breiland et al ("A virtual interface method for extracting growth rates and high temperature optical constants from thin semiconductor films using in situ normal incidence reflectance", Journal of Applied Physics, 1995)

This is part of the qncmbe package. Please see the example file

'''

# Non-standard library imports (included in setup.py)
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
        self.n = {}
        self.k = {}
        
    def set_nk_at_wavelength(self, wvln, n, k):
        self.n[wvln] = n
        self.k[wvln] = k

class FittableParameter():
    def __init__(self, val0, is_fitted = False):
        self.valopt = val0
        self.val0 = val0
        self.is_fitted = is_fitted
                
def calc_reflectance(time, n, k, ns, ks, G, s, wvln):
        
    N = n - 1j*k
    Ns = ns - 1j*ks

    r_inf = (1 - N)/(1 + N)
    r_i = (N - Ns)/(N + Ns)

    exp_factor = r_i*np.exp(-1j*4.0*np.pi*N*G*time/wvln)

    r = (r_inf + exp_factor)/(1 + r_inf*exp_factor)

    return s*np.absolute(r)**2

def fit_reflectance(refl, time, pars_guess):
    '''
    - refl and time should be numpy arrays with the reflectancs vs time data
    - pars_guess should be a dictionary of FittableParameter objects with keys equal to {'n', 'k', 'ns', 'ks', 'G', 's', 'wvln'}
    '''

    pfit_guess = [] # Array of initial guesses for fitted parameters
    pfit_keys = [] # Array of names of fitted parameters
    pfix = {} # Dictionary of fixed parameters
    
    for p in pars_guess:
        if pars_guess[p].is_fitted:
            pfit_guess.append(pars_guess[p].val0)
            pfit_keys.append(p)
        else:
            pfix[p] = pars_guess[p].val0

    refl_func = lambda t, *p_arr: calc_reflectance(t, **{k: p for k, p in zip(pfit_keys, p_arr)}, **pfix)

    rel_time = time - time[0]

    try:
        popt, pcov = opt.curve_fit(refl_func, rel_time, refl, p0 = pfit_guess)
    except:
        pars_opt = pars_guess
        refl_fit = refl_func(rel_time, *pfit_guess)
        print("WARNING: fit failed.")
        return pars_opt, refl_fit

    pars_opt = {**pars_guess}
    for k,p in zip(pfit_keys, popt):
        pars_opt[k].valopt = p

    refl_fit = refl_func(rel_time, *popt)

    return pars_opt, refl_fit

def print_fitted_value(name, x, units = '', print_error = True):
    
    if units != '':
        pad_units = ' ' + units
    else:
        pad_units = ''

    if x.is_fitted:
    
        if (np.abs(x.val0) > 1e-20) and print_error:
            x_err = (x.valopt - x.val0)*100/x.val0
            string = '{} = {:.5f}{} ({:.5f} % away from initial guess of {:.5f}{})'.format(name, x.valopt, pad_units, x_err, x.val0, pad_units)
        else:
            string = '{} = {:.5f}{} (Initial guess: {:.5f}{})'.format(name, x.valopt, pad_units, x.val0, pad_units)
        
    else:
        string = '{} = {:.5f}{} (Fixed)'.format(name, x.val0, pad_units)
        
    return string + '\n'

class Layer():
    def __init__(self, material, material_beneath, growth_rate, t_start = -np.inf, t_end = np.inf):
        '''
        - material and material_beneath should be of class Material
        - growth_rate should be a float (if using angtroms, should call use_angstroms_for_structure())
        - If t_start and t_end are specified, will automatically use them to restrict the data provided in set_refl_data()
        '''
        self.material = material
        self.material_beneath = material_beneath
        self.G = growth_rate

        self.t_start = t_start
        self.t_end = t_end

        self.name = ''

        self.wvln_scale = 1.0
        self.use_angstroms = False
                
    def set_name(self, name):
        self.name = name                  
    
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

    def set_refl_pars_guess(self, fit_pars = 'ns,ks,G,s'):
        '''
        fit_pars should be a comma-separated list of parameters to fit
        e.g., 'ns,ks,G,s' or 'n,k,ns,ks,s'
        All other parameters will be held fixed.
        '''
        self.refl_pars_guess = {}
        
        for wvln in self.refl_data:

            if self.material_beneath is not None:
                ns0 = self.material_beneath.n[wvln]
                ks0 = self.material_beneath.k[wvln]
            else:
                ns0 = 1.0
                ks0 = 0.0

            vals_dict = {
                'n': self.material.n[wvln], 
                'k': self.material.k[wvln],
                'ns': ns0, 
                'ks': ks0,
                'G': self.G,
                's': 1.0,
                'wvln': float(wvln)*self.wvln_scale
            }

            self.refl_pars_guess[wvln] = {k: FittableParameter(vals_dict[k]) for k in vals_dict}

            for key in fit_pars.split(','):
                self.refl_pars_guess[wvln][key].is_fitted = True
            
    def set_pars_to_fit(self,fit_pars = 'n,k,ns,ks,G,s'):
        '''
        fit_pars should be a comma-separated list of parameters to fit
        e.g., 'ns,ks,G,s' or 'n,k,ns,ks,s'
        All other parameters will be held fixed.
        '''
        self.set_refl_pars_guess(fit_pars)
    
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
            
            string += '\nWavelength = {} nm'.format(wvln)
            string += '\n'
            for key in ['n','k','ns','ks']:
                string += print_fitted_value(key, pars_fit[key], print_error = False)

            G_units = 'Å/s' if self.use_angstroms else 'nm/s'

            string += print_fitted_value('G', pars_fit['G'], units = G_units)
            string += print_fitted_value('s', pars_fit['s'], print_error = False)
            
        string += '------------------------------\n'

        return string

    def print_growth_rate_summary(self):

        string = '------------------------------\n'
        string += 'Layer: {}\n'.format(self.name)

        for wvln in self.refl_fit:
            
            pars_fit = self.refl_pars_fit[wvln]
            
            string += 'Wavelength = {} nm\n'.format(wvln)

            G_units = 'Å/s' if self.use_angstroms else 'nm/s'
            string += print_fitted_value('G', pars_fit['G'], units = G_units)
        
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
    def __init__(self):
        
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

    def add_layer(self, name, material, material_beneath, growth_rate, t_start, t_end):
        
        new_layer = Layer(material, material_beneath, growth_rate, t_start, t_end)

        if name in self.layer_names:
            raise Exception(f'Layer name "{name}" already used. Each layer must have a unique name.')
        
        new_layer.set_name(name)
                
        new_layer.set_refl_data(self.t_data, self.R_data)
        new_layer.use_angstroms_for_structure(self.use_angstroms)
        new_layer.set_refl_pars_guess()
        
        self.layers.append(new_layer)
        self.layer_names.append(name)
        
    def set_pars_to_fit(self, fit_pars):
        '''
        fit_pars should be a comma-separated list of parameters to fit
        e.g., 'ns,ks,G,s' or 'n,k,ns,ks,s'
        All other parameters will be held fixed.
        '''
        for layer in self.layers:
            layer.set_pars_to_fit(fit_pars)

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

    def get_fit_convergence(self, layer_name, t_buffer, t_step, parameter = 'G'):
        layer = self.get_layer_by_name(layer_name)

        self.update_refl_data()

        t_out = []
        p_out = {wvln: [] for wvln in self.R_data}
        
        t_start = layer.t_start
        t_end = layer.t_end

        t = t_start + t_buffer

        while (t <= t_end) and (t <= self.t_data[-1]):
            layer.t_end = t
            layer.set_refl_data(self.t_data, self.R_data)
            layer.calc_refl_fit()

            t_out.append(t)
            pfit = layer.refl_pars_fit

            for wvln in self.R_data:
                p_out[wvln].append(layer.refl_pars_fit[wvln][parameter].valopt)

            t += t_step
        layer.t_end = t_end
        layer.set_refl_data(self.t_data, self.R_data)
        layer.calc_refl_fit()

        t_out = np.array(t_out)
        p_out = {wvln: np.array(p_out[wvln]) for wvln in p_out}

        return t_out, p_out

    def plot_fit_convergence(self, layer_name, t_buffer, t_step, parameter):

        t, p = self.get_fit_convergence(layer_name, t_buffer, t_step, parameter)

        fig, ax = plt.subplots()
        
        n = 0
        for wvln in p:
            if wvln in wvln_colors_dark:
                color = wvln_colors_dark[wvln]
            else:
                color = f'C{n}'
                n+=1
            ax.plot(t - t[0] + t_buffer, p[wvln], '.-', label = wvln + " nm", color = color)

        G_units = 'Å/s' if self.use_angstroms else 'nm/s'

        units = f' ({G_units})' if parameter == 'G' else ''

        ax.set_xlabel("Time relative to layer start (s)")
        ax.set_ylabel(f"Fitted value {parameter}{units}")
        ax.legend()

        ax.set_title(f"Layer {layer_name}: fit convergence")

        return fig, ax
        