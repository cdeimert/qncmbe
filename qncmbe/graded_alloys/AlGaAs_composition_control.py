'''
Functions for generating smooth composition profiles in AlGaAs by varying the Al cell temperature as a function of time
'''

# Non-standard library imports (included in setup.py)
import numpy as np
from scipy.integrate import cumtrapz
import scipy.signal as sig
from scipy.special import lambertw

a_GaAs = 0.565338  # nm
a_perp_AlAs = 0.566918  # nm

# Needed to map cell names into Molly commands for shutter control
shutter_location = {
    'Ga1': 'Ga1_tip',
    'Ga2': 'Ga2_tip',
    'Al1': 'Al1_tip',
    'Si1': 'Si1_base',
    'As1': 'As1_valve'
}

def flux_to_temperature(flux_in, A, B, C):
    
    arg = -2*B*(flux_in/(A*C))**2
    
    return np.real(-2*B/lambertw(arg,-1))

def temperature_to_flux(T_in, A, B, C):
    return A*C*np.exp(-B/T_in)/np.sqrt(T_in)

def calc_Al_shutter_transient(t, s, K_sh, t_sh, zeta_sh, T_sh, n_per = 1):
    '''
    t, s are the time and shutter signals
    The rest of the inputs are constants defining the dynamic response
    
    n_per is the number of repetitions. E.g., n_per = 10 will give the response after the input has already been applied 9 times
    Useful for approximating a periodic system
    
    Assumes t is equally spaced!
    
    Also implicitly assumes that the Al shutter is *open* and at equilibrium for t < 0
    '''

    w_sh = 2*np.pi/t_sh

    num = [-K_sh*zeta_sh*w_sh*T_sh, -T_sh*w_sh**2]
    den = [1, 2*zeta_sh*w_sh, w_sh**2]

    shutter_system = sig.lti(num, den)

    if n_per > 1:
        s_in = np.concatenate([s[:-1] for n in range(n_per)] + [s[-1:]])
        t_in = np.concatenate([t[:-1] + n*t[-1] for n in range(n_per)] + [t[-1:]*n_per])
    else:
        s_in = s[:]
        t_in = t[:]

    t_out, T_out, x_out = sig.lsim(shutter_system, 1-s_in, t_in)
    
    return t, -T_out[-len(t):]

def calc_inverse_Al_dynamics(t, T_targ, K, t0, zeta, n_per = 1):
    '''
    Inverse of the second order dynamical model for tha Al cell
    Gives the temperature input required for a target temperature output

    t is the time signal (Assumes t is equally spaced!)
    The rest of the inputs are constants defining the dynamic response
    
    n_per is the number of repetitions. E.g., n_per = 10 will give the response after the input has already been applied 9 times
    Useful for approximating a periodic system
    '''
    
    T_init = T_targ[0]
       
    # Extend over n_per periods
    if n_per > 1:
        T_targ_ext = np.concatenate([T_targ[:-1] for n in range(n_per)] + [T_targ[-1:]])
        t_ext = np.concatenate([t[:-1] + n*t[-1] for n in range(n_per)] + [t[-1:]*n_per])
    else:
        T_targ_ext = T_targ[:]
        t_ext = t[:]
        
    # Subtract initial value
    T_targ_ext -= T_init
    
    w0 = 2*np.pi/t0
     
    kz = K*zeta

    a = 1/(kz*w0)
    b = (2*kz*zeta - 1)/(kz**2)
    c = (kz**2 - 2*kz*zeta + 1)*w0/(kz**3)
    tau = kz/w0

    # Derivative part
    dt = t[1] - t[0]
    #print(A, B, C, tau)
    
        
    T_der = a*np.gradient(T_targ_ext, dt, edge_order = 2)
    
    # Gain part
    
    T_gain = b*T_targ_ext
    
    # Integral part
    num = [c]
    den = [1.0, 1.0/tau]
    int_sys = sig.lti(num, den)
    
    t_int, T_int, x_out = sig.lsim(int_sys, T_targ_ext, t_ext)
    
    T_in = T_der + T_gain + T_int + T_init
            
    return T_in[-len(t):]

class Growth_step():
    def __init__(self, open_shutters, t, T_Al, name = 'Growth step'):
        self.name = name
        self.open_shutters = open_shutters # List of which cell shutters are open
        self.t = t # Array of time points
        self.T_Al = T_Al # Array of desired Al melt temperatures

class Growth():
    def __init__(self, Ga_cell, GR_GaAs, Al_cell_pars, dry_run = False):
        
        self.Ga_cell = Ga_cell # String (either 'Ga1' or 'Ga2')
        self.GR_GaAs = GR_GaAs # 'nm/s'
        
        self.flux_Ga = 4*GR_GaAs/(a_GaAs**3) # flux in nm^-2.s^-1
        
        self.Al_cell_pars = Al_cell_pars 
            # Should be a dictionary like
            # {
            #   'static': [A,B,C],
            #   'shutter': [K_sh, t_sh, zeta_sh, T_sh],
            #   'dynamic': [K, t0, zeta]
            # }
            # 
        
        self.dry_run = dry_run # Set true to generate recipes where only Al shutter is opened
        
        self.steps = []
        
        self.t_total = 0.0
        self.set_dt_max(0.5)        
        
    def update_t(self):
        num_t = int(self.t_total/self.dt_max) + 1
        self.t = np.linspace(0, self.t_total, num_t)
        
    def get_t(self):
        return self.t
        
    def set_dt_max(self, dt_max):
        self.dt_max = dt_max
        self.update_t()
        
    def add_growth_step(self, open_shutters, t, T_Al, name = 'Growth step'):
        
        t_rel = t - t[0]
        
        self.steps.append(Growth_step(open_shutters, self.t_total + t_rel, T_Al, name))
        
        self.t_total += t_rel[-1]
        
        self.update_t()
        
        print("Adding step '{}'. Duration = {:.2f} s".format(name, t_rel[-1]))

    def add_AlGaAs_step(self, z, x, Si_doped = False, name = 'AlGaAs layer'):
        
        open_shutters = [self.Ga_cell, 'Al1', 'As1']
        
        if Si_doped:
            open_shutters += ['Si1']

        flux_Al = x*self.flux_Ga/(1 - x)
        T_Al = flux_to_temperature(flux_Al, *self.Al_cell_pars['static'])

        GR_AlGaAs = (a_perp_AlAs*flux_Al + a_GaAs*self.flux_Ga)*(a_GaAs**2)/4

        if np.isscalar(GR_AlGaAs):
            duration = z/GR_AlGaAs

            t = np.array([0,duration])
            T_Al_vs_t = np.array([T_Al, T_Al])

        else:
            t = cumtrapz(1/GR_AlGaAs, z, initial= 0.0)
            T_Al_vs_t = np.copy(T_Al)

        self.add_growth_step(open_shutters, t, T_Al_vs_t, name)
        
    def add_GaAs_step(self, z, x, Si_doped = False, name = 'GaAs layer'):
        
        open_shutters = [self.Ga_cell, 'Al1', 'As1']
        
        if Si_doped:
            open_shutters += ['Si1']

        flux_Al = x*self.flux_Ga/(1 - x)
        T_Al = flux_to_temperature(flux_Al, *self.Al_cell_pars['static'])

        GR_AlGaAs = self.GR_GaAs

        duration = z/GR_AlGaAs

        t = np.array([0,duration])
        T_Al_vs_t = np.array([T_Al, T_Al])

        self.add_growth_step(open_shutters, t, T_Al_vs_t, name)
        
        
    def add_smooth_ramp_step(self, duration, xi, xf, Si_doped = False, dt = 0.5, name = 'Smooth ramp'):
        # Will generate a smooth transition in the desired Al temperature (continuous derivative)
        # Becomes trivial if xi = xf, but can be used for, e.g., delta doping
        
        open_shutters = ['As1']
        if Si_doped:
            open_shutters += ['Si1']
        
        flux_i = xi*self.flux_Ga/(1 - xi)
        flux_f = xf*self.flux_Ga/(1 - xf)
        Ti = flux_to_temperature(flux_i, *self.Al_cell_pars['static'])
        Tf = flux_to_temperature(flux_f, *self.Al_cell_pars['static'])

        num_t = int(duration/dt) + 1
        t = np.linspace(0, duration, num_t)

        T = np.zeros_like(t)

        mask = t <= duration/2
        T[mask] = Ti + 2*(Tf  - Ti)*(t[mask]/duration)**2
        T[~mask] = Tf + 2*(Ti  - Tf)*(t[~mask]/duration - 1)**2

        self.add_growth_step(open_shutters, t, T, name)

    def add_PQW_step(self, L_QW, x_min, x_max, Si_doped = False, num_z = 2000, name = 'PQW'):

        z = np.linspace(-L_QW/2, L_QW/2, num_z)

        x = (x_max - x_min)*(2*z/L_QW)**2 + x_min

        self.add_AlGaAs_step(z - z[0], x, Si_doped, name)

    def add_half_PQW_step(self, L_QW, x_min, x_max, Si_doped = False, barrier_first = False, num_z = 2000, name = 'Half PQW'):

        if barrier_first:
            z = np.linspace(0, L_QW, num_z)
        else:
            z = np.linspace(-L_QW, 0, num_z)

        x = (x_max - x_min)*(z/L_QW)**2 + x_min

        self.add_AlGaAs_step(z - z[0], x, Si_doped, name)

    def get_T_Al(self):
        
        t_raw = np.concatenate([step.t for step in self.steps])
        T_raw = np.concatenate([step.T_Al for step in self.steps])
        
        return np.interp(self.t, t_raw, T_raw)
    
    def get_shutter_status(self, cell):
        
        t_raw = []
        s_raw = []
        
        for step in self.steps:
            t_raw.append(step.t)
            
            if cell in step.open_shutters:
                s_raw.append(np.ones_like(step.t))
            else:
                s_raw.append(np.zeros_like(step.t))
        
        t_raw = np.concatenate(t_raw)
        s_raw = np.concatenate(s_raw)
        
        return np.interp(self.t, t_raw, s_raw)        
    
    def get_Al_flux(self):
        
        T = self.get_T_Al()
        s = self.get_shutter_status('Al1')
        
        flux = s*temperature_to_flux(T, *self.Al_cell_pars['static'])
        
        return flux
    
    def get_Al_composition(self):
        
        flux_Al = self.get_Al_flux()
        s_Ga = self.get_shutter_status('Ga1')
        return flux_Al/(flux_Al + self.flux_Ga*s_Ga)
        
    
    def get_cumulative_thickness(self):
        
        s_Ga = self.get_shutter_status('Ga1')
        flux_Al = self.get_Al_flux()
        GR_AlGaAs = (a_perp_AlAs*flux_Al + a_GaAs*self.flux_Ga*s_Ga)*(a_GaAs**2)/4
        
        z = cumtrapz(GR_AlGaAs, self.t, initial= 0.0)
        
        return z
        
    def get_Al_shutter_transient(self, n_per = 1):
        
        s = self.get_shutter_status('Al1')
        
        t, T_s = calc_Al_shutter_transient(self.t, s, *self.Al_cell_pars['shutter'], n_per)
        
        return T_s
    
    def get_T_in(self,n_per = 1, include_shutter = True):
        # Calculate Al input temperature sequence for the desired flux profile
        
        T_Al = self.get_T_Al()
        
        if include_shutter:
            T_s = self.get_Al_shutter_transient(n_per)
        else:
            T_s = np.zeros_like(T_Al)
        
        
        T_in = calc_inverse_Al_dynamics(self.t, T_Al - T_s, *self.Al_cell_pars['dynamic'], n_per)
        
        return T_in
    
    def generate_Molly_code(self, dry_run = False, n_per = 1):
        
        header = "\ndouble t0;"
        header += "\nt0 = t;"
        header += "\n\nset_ramp(Al1_base, 0.0);"
        header += "\n"
        
        times = []
        commands = []
        
        # Shutter commands
        for step in self.steps:
            string = "\n\n/********** {} **********/".format(step.name)
            string += '\necho("Starting {}");'.format(step.name)
            string += '\n'
            string += '\nset_sh('

            if dry_run: # If dry run, ignore all cells other than Al
                if 'Al1' in step.open_shutters:
                    string += shutter_location['Al1']
            else:
                n = 0
                for cell in step.open_shutters:
                    if n > 0:
                        string += ', '
                    string += shutter_location[cell]
                    n += 1
                    
                if 'As1_valve' not in string:
                    print("WARNING: As shutter closed in {}".format(step.name))
                    

            string += ");\n"
            
            commands.append(string)
            times.append(step.t[0])
            
        # Al temperature commands
        
        T_in = self.get_T_in(n_per)
        t = self.get_t()
        
        for t_val, T_val in zip(t,T_in):
            times.append(t_val)
            commands.append("\nset_temp(Al1_base, {:e});".format(T_val - 273.15))
        
        # Sort the lists in order of time
        times = np.array(times)
        
        inds = np.argsort(times)

        times_copy = list(times)
        commands_copy = list(commands)

        for i, i_sort in enumerate(inds):
            times[i] = times_copy[i_sort]
            commands[i] = commands_copy[i_sort]
            
        # Print Molly commands in sequence with appropriate wait steps
        
        out_str = header
        for t_val, comm in zip(times[:-1], commands[:-1]):
            out_str += "\n\nsleep({:.8f} - (t - t0));\n".format(t_val)
            out_str += comm
            
        out_str += "\n\nsleep({:.8f} - (t - t0));\n".format(times[-1])
        
        return out_str