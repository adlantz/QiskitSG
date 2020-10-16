#!/usr/bin/env python

""""TFIMED.py
    Chris Herdman
    06.07.2017
    --Classes \& functions for eact enumeration of the Hilber space of
        transverse field Ising models
    --Requires: numpy, scipy.sparse, scipy.linalg, progressbar

    --Edited down to bare funcionality for qiskit project by Asher Lantz Oct. 2020
"""

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as spla
import progressbar

###############################################################################
class Lattice:
    """Define a lattice"""
    def __init__(self, L, PBC=True):
        
        # Assigned parameters
        self.L = L                  # list of linear dimension for each dim.
        self.PBC = PBC              # Boundary Conditions
        
        # Derived parameters
        self.N = np.prod(self.L)    # Number of spins
        self.D = len(L)             # spatial dimensionality
        self.N_links = ( self.D*self.N      # Number of nearest neighbor links
                        - int(not self.PBC)*( 1 if (self.D == 1)
                            else int(not self.PBC)*(sum(L)) ) )                       
    

###############################################################################
class IsingBasis:
    """Basis for the Hilbert space of an Ising Model"""
    def __init__(self,lattice):
        self.N = lattice.N      # Number of spins
        self.M = 2**lattice.N   # Size of basis
    
    def state(self,index):
        """Returns the state associated with index"""
        return np.array(list(bin(index)[2:].zfill(self.N))).astype(int)
    
    def spin_state(self,index):
        """Returns the spin state associated with index"""
        return 2*self.state(index) - 1
    
    def index(self,state):
        """Returns the index associated with state"""
        return int(''.join(state.astype(str)),2)
    
    def flip(self,state,i):
        """Flips ith spin in state"""
        state[i] = (state[i]+1)%2
    

###############################################################################
def JZZ_SK_ME(basis,J):
    """ Computes matrix elements for the SK interactions
        and returns each as a 1D np.array
        --JZZ = \sum_{i,j} J_{ij}\sigma^z_i \sigma^z_j"""
    
    JZZ = np.zeros(basis.M)
    shift_state = np.zeros(basis.N,dtype=int)
    for b in range(basis.M):
        state = basis.spin_state(b)
        for shift in range(1,basis.N//2+1):
            shift_state[shift:] = state[:-shift]
            shift_state[:shift] = state[-shift:]
            if (basis.N%2 == 0) and (shift == basis.N//2):
                JZZ[b] = JZZ[b] + 0.5*np.dot(J[shift-1,:]*shift_state,state)
            else:
                JZZ[b] = JZZ[b] + np.dot(J[shift-1,:]*shift_state,state)

    return JZZ

###############################################################################
def JZZ_SK(basis,J):
    """Builds matrices for infinite range zz interactions
        and returns each as a scipy.sparse.coo_matrix
        --JZZ = \sum_{i,j} J_{ij}\sigma^z_i \sigma^z_j"""
    JZZ_ME = JZZ_SK_ME(basis,J)
    I = np.arange(basis.M)
    return sparse.coo_matrix((JZZ_ME,(I,I)),shape=(basis.M,basis.M))

###############################################################################
def Jij_instance(N,J,dist,seed,even):
    """Generates an random instance of couplings"""

    np.random.seed(seed)

    if dist == "bimodal":
        if even:
            # Generates Jij matrix with even numbers of ferromagnetic and anti-ferromagnetic bonds
            num_of_bonds = (N*(N-1))//2
            if N%4 == 0:
                a1 = [-1 for i in range(num_of_bonds//2)]
            else:
                a1 = [-1 for i in range((num_of_bonds//2) + 1)]
            a2 = [1 for i in range(num_of_bonds//2)]
            a = list(np.random.permutation(a1+a2))
            Jij = [a[(N*j):N*(j+1)] for j in range(N//2)]
            if N%2 == 0:
                Jij[(N//2) - 1] += Jij[(N//2) - 1]
            Jij = np.array(Jij)
            
        else:
            Jij = np.random.choice([-1,1],size=(N//2,N))
            if N%2 == 0:
                Jij[-1,N//2:] = Jij[-1,:N//2]

    elif dist == "normal":
        Jij = np.random.normal(scale=J/np.sqrt(N),size=(N//2,N))
        if N%2 == 0:
            Jij[-1,N//2:] = Jij[-1,:N//2]

    return Jij

