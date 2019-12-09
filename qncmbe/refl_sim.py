# Non-standard library imports (included in setup.py)
import numpy as np


class Material():
    def __init__(self, name):
        self.name = name
        self.N = {}
        
    def set_N_at_wavelength(self, wavelength, N):
        self.N[str(wavelength)] = N

class Layer():
    def __init__(self, material, thickness, growth_rate):
        self.thickness = thickness
        self.material = material
        self.N = self.material.N
        self.growth_rate = growth_rate
        
        self.growth_time = thickness/growth_rate
        
    def set_transfer_matrix(self, transfer_matrix):
        self.transfer_matrix = transfer_matrix
        
    def set_vacuum_interface_matrix(self, vacuum_interface_matrix):
        self.vacuum_interface_matrix = vacuum_interface_matrix
        
    def set_layer_matrix(self, layer_matrix, t):
        self.layer_matrix = layer_matrix
        self.t = t
        
    def set_reflectance(self, reflectance):
        self.reflectance = reflectance

        
class Structure():
    def __init__(self, substrate_material, num_t = 1000):
        self.substrate_material = substrate_material
        self.num_t = num_t
        self.layers = []
        
        self.wavelength_scale = 1.0 # Assumes wavelengths and structure are both in nm
        # To change structure to angstrom, use use_angstroms_for_structure()
    
    def use_angstroms_for_structure(self):
        self.wavelength_scale = 0.1
    
    def set_wavelength(self, wavelength):
        self.wavelength = str(wavelength)
        
    def add_layer(self, material, thickness, growth_rate):
        if not self.layers:
            self.layers.append(Layer(material, 
                                     thickness, 
                                     growth_rate))
        else:
            self.layers.append(Layer(material, 
                                     thickness, 
                                     growth_rate))
            
    def calculate_transfer_matrices(self):
        
      
        for i in range(len(self.layers)):
            
            Ni = self.layers[i].material.N[self.wavelength]
            if i != 0:
                Nim1 = self.layers[i-1].material.N[self.wavelength]
            
            # Transfer matrices
            if i == 0:
                T0 = np.zeros((2,2), dtype = complex)
                T0[0,0] = Ni + self.substrate_material.N[self.wavelength]
                T0[0,1] = Ni - self.substrate_material.N[self.wavelength]
                T0[1,0] = T0[0,1]
                T0[1,1] = T0[0,0]

                T0 /= 2*Ni

                self.layers[0].set_transfer_matrix(T0)
                
            else:
                
                T = np.matmul(self.layers[i-1].layer_matrix[-1,:,:], 
                              self.layers[i-1].transfer_matrix)
                
                I = np.zeros((2,2), dtype = complex)
                I[0,0] = Ni + Nim1
                I[0,1] = Ni - Nim1
                I[1,0] = I[0,1]
                I[1,1] = I[0,0]
                
                I /= 2*Ni
                
                T = np.matmul(I, T)
                
                self.layers[i].set_transfer_matrix(T)
                
            # Vacuum interface matrices
            I = np.zeros((2,2), dtype = complex)
            I[0,0] = 1.0 + Ni
            I[0,1] = 1.0 - Ni
            I[1,0] = I[0,1]
            I[1,1] = I[0,0]

            I /= 2
            
            self.layers[i].set_vacuum_interface_matrix(I)
            
            # Layer matrices                                 

            d = np.linspace(0, self.layers[i].thickness, self.num_t)
            
            t = d/self.layers[i].growth_rate
            
            if i != 0:
                t += self.layers[i-1].t[-1]
            
            wl = float(self.wavelength)/self.wavelength_scale

            exp_fact = np.exp(1j*2*np.pi*Ni*d/wl)
            
            L = np.zeros((self.num_t,2,2), dtype = complex)
            
            L[:,0,0] = exp_fact
            L[:,0,1] = 0.0 + 1j*0
            L[:,1,0] = 0.0 + 1j*0
            L[:,1,1] = 1/exp_fact
            
            self.layers[i].set_layer_matrix(L,t)
    
    def calculate_reflectance(self, wavelength):
        
        self.set_wavelength(wavelength)
        
        self.calculate_transfer_matrices()
        
        t_total = np.array([])
        R_total = np.array([])
        
        for layer in self.layers:
            M = np.zeros((self.num_t,2,2), dtype = complex)
            
            M = np.matmul(layer.layer_matrix, layer.transfer_matrix)
            M = np.matmul(layer.vacuum_interface_matrix, M)
            
            r = M[:,1,0]/M[:,0,0]
            
            R = np.abs(r)**2
            
            layer.set_reflectance(R)
        
            t_total = np.concatenate((t_total, layer.t))
            R_total = np.concatenate((R_total, layer.reflectance))
            
        return t_total, R_total