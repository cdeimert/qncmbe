import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
import scipy.signal as sig

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

# def get_restricted_refl_func(**kwargs):
#     # 'Magic' function to create a new version of calc_reflectance with some arguments fixed.
#     # E.g., if you call get_restricted_refl_func(s = 1.0, wavelen = 470.0), you are returned a function
#     #   refl_func(time, n, k, ns, ks, G) which is equivalent to calc_reflectance(time, n, k, ns, ks, 1.0, 470.0)
#     #
#     # This is needed for the scipy curve fitting routine.

#     funcstr = '''def refl_func({p}):\n\treturn calc_reflectance({q})'''

#     all_vars = ['time', 'n', 'k', 'ns', 'ks', 'G', 's', 'wvln']
#     fixed_vars = list(kwargs.keys())

#     args = []
#     fit_vars = []
#     for var in all_vars:
#         if var in fixed_vars:
#             args.append(str(kwargs[var]))
#         else:
#             args.append(var)
#             fit_vars.append(var)

#     args = ', '.join(args)
#     fit_vars = ', '.join(fit_vars)

#     func_def = funcstr.format(p=fit_vars, q=args)
#     exec(func_def, globals())

#     return refl_func

def dict_to_list(in_dict, keys):
	return [in_dict[key] for key in keys]

def list_to_dict(in_list, keys):
	return {k:v for k,v in zip(keys, in_list)}

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
    #refl_func = get_restricted_refl_func(**fixed_vals)
    p0 = dict_to_list(par_guess, par_keys[p_fit])

    rel_time = time - time[0]

    try:
        p_opt, p_cov = opt.curve_fit(refl_func, rel_time, refl, p0 = p0)
    except:
        refl_pars_fit = refl_pars_guess.copy()
        refl_fit = calc_reflectance(rel_time, **par_guess)
        print("WARNING: fit failed.")
        return refl_pars_fit, refl_fit

    #p_err = np.sqrt(np.diag(p_cov))

    par_opt = list_to_dict(p_opt, par_keys[p_fit])
    #par_err = list_to_dict(p_err, par_keys[p_fit])
    
    for key in par_keys[p_fix]:
        par_opt[key] = par_guess[key]
  
    refl_pars_fit = refl_pars_guess.copy()

    refl_pars_fit.N.value = par_opt['n'] - 1j*par_opt['k']
    refl_pars_fit.Ns.value = par_opt['ns'] - 1j*par_opt['ks']
    refl_pars_fit.G.value = par_opt['G']
    refl_pars_fit.s.value = par_opt['s']
    refl_pars_fit.wvln.value = par_opt['wvln']
    
    #refl_fit = refl_func(rel_time, **par_opt)
    refl_fit = calc_reflectance(rel_time, **par_opt)

    #for key in par_keys[p_fix]:
    #    par_opt[key] = par_guess[key]
    #    par_err[key] = 0.0

    #par_opt_rel = {key: (par_opt[key] - par_guess[key])/par_guess[key] for key in par_guess}
    #par_err_rel = {key: par_err[key]/par_guess[key] for key in par_guess}

    #fit_error = np.average((refl_fit - refl)**2)

    #fit_results = { 'par_opt': par_opt, 
    #                'par_err': par_err, 
    #                'par_opt_rel': par_opt_rel,
    #                'par_err_rel': par_err_rel,
    #                'refl_fit': refl_fit,
    #                'fit_error': fit_error}

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
    def __init__(self, material, thickness, t_total):
        self.material = material
        self.thickness = thickness
        self.t_total = t_total
        self.G = thickness/t_total
        
        self.t_buffer = 10.0
        self.t_start = 0.0
        self.t_end = 0.0

        self.wvln_scale = 1.0
        self.use_angstroms = False
        
    def set_t_buffer(self, t_buffer):
        self.t_buffer = t_buffer
        self.calc_t_end()
        
    def set_refl_t_start(self, t_start):
        self.t_start = t_start
        self.calc_t_end() 
        
    def calc_t_end(self):
        self.t_end = self.t_start + self.t_total - self.t_buffer
        
    def set_name(self, name):
        self.name = name
        
    def set_material_beneath(self, material):
        self.material_beneath = material                       
    
    def set_refl_data(self, raw_t, raw_R):
        # raw_R should be a dictionary of numpy arrays at different wavelengths
        mask = (raw_t > self.t_start) & (raw_t < self.t_end)
        
        self.t_data = raw_t[mask]
        self.refl_data = {wvln: raw_R[wvln][mask] for wvln in raw_R}
    
    def use_angstroms_for_structure(self, use_angstroms = True):
        self.use_angstroms = use_angstroms

        if use_angstroms:
            self.wvln_scale = 10.0
        else:
            self.wvln_scale = 1.0

    def set_refl_pars_guess(self, fit_type = 'fix nk'):
        
        self.refl_pars_guess = {}
        
        for wvln in self.refl_data:
            self.refl_pars_guess[wvln] = Refl_parameters(self.material.N[wvln], 
                                                         self.material_beneath.N[wvln],
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
        
        for wvln in self.refl_data:
            ax.plot(self.t_data, self.refl_data[wvln], '.', label = wvln + " nm data")
            ax.plot(self.t_data, self.refl_fit[wvln], '-', label = wvln + " nm fit")
        
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
        self.use_angstroms = False
        self.fit_type = 'fix nk'
        
    def set_refl_data(self, t_data, R_data):
        self.t_data = t_data
        self.R_data = R_data
                
    def set_t_buffer(self, t_buffer):
        for layer in self.layers:
            layer.set_t_buffer(t_buffer)      
           
    def use_angstroms_for_structure(self, use_angstroms = True):
        self.use_angstroms = use_angstroms
        for layer in self.layers:
            layer.use_angstroms_for_structure(use_angstroms)
            layer.set_refl_pars_guess(self.fit_type)

    def add_layer(self, name, material, thickness, t_total, t_start):
        
        new_layer = Layer(material, thickness, t_total)
        new_layer.set_name(name)
        new_layer.set_refl_t_start(t_start)
                       
        if self.layers:
            new_layer.set_material_beneath(self.layers[-1].material)
        else:
            new_layer.set_material_beneath(self.substrate)      
        
        new_layer.set_refl_data(self.t_data, self.R_data)
        new_layer.use_angstroms_for_structure(self.use_angstroms)
        new_layer.set_refl_pars_guess()
        
        self.layers.append(new_layer)
        
        
    def set_fit_type(self, fit_type):
        for layer in self.layers:
            layer.set_fit_type(fit_type)

        self.fit_type = fit_type

    def calc_refl_fits(self):
        for layer in self.layers:
            layer.calc_refl_fit()
            
    def display_fit_results(self):
        for layer in self.layers:
            layer.plot_refl_fit()
            print(layer.print_refl_fit())

    def print_growth_rate_summary(self):
        for layer in self.layers:
            print(layer.print_growth_rate_summary())
            