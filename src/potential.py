import numpy as np
class Potential:
    """ Potential class. Find the force acting on the particles
    given a potential.
    """
    def __init__(self):
        pass
        
    def __call__(self, r):
        raise NotImplementedError ("Class {} has no instance '__call__'."
                                   .format(self.__class__.__name__))
                     
    @staticmethod              
    def potentialEnergy(u, cutoff):
        raise NotImplementedError ("Class {} has no instance 'potentialEnergy'."
                                   .format(self.__class__.__name__))

class LennardJones(Potential):
    """ The Lennard-Jones potential. Taking the form
        U(r) = 4ε((σ/r)^12 - (σ/r)^6)
    
    Parameters
    ----------
    solver : obj
        class object defined by moleculardynamics.py. Takes the MDSolver 
        class as argument
    cutoff : float
        cutoff distance: maximum length of the interactions. 3 by default.
    """
    def __init__(self, solver, cutoff=3):
        self.cutoff = cutoff
        self.boundaries = solver.boundaries
        
    def __repr__(self):
        """ Representing the potential.
        """
        return "Lennard-Jones potential"
        
    def calculateDistanceMatrix(self, r):
        """ Compute the distance matrix (squared) at timestep t. In the
        integration loop, we only need the distance squared, which 
        means that we do not need to take the square-root of the 
        distance. We also exploit Newton's third law and calculate the
        needed forces just once. Additionally, we only care about the
        particles within a distance specified by the cutoff distance.
        
        Parameters
        ----------
        r : ndarray
            spatial coordinates at some timestep
            
        Returns
        -------
        dr : ndarray
            distance vector between all the particles
        distanceSqrd : ndarray
            distance between all particles squared
        distancePowSixInv : ndarray
            distance between all particles to the power of six inverse
        distancePowTwelveInv : ndarray
            distance between all particles to the power of twelve inverse
        """
        par, dim = r.shape
        half = par*par // 2
        x, y = r[:,np.newaxis,:], r[np.newaxis,:,:]
        drAll = x - y
        drAll = self.boundaries.checkDistance(drAll)
        distanceSqrdAll = np.einsum('ijk,ijk->ij',drAll,drAll)        # r^2
        upperTri = np.triu_indices(par, 1)
        distanceSqrdHalf = distanceSqrdAll[upperTri]
        drHalf = drAll[upperTri]
        indices = np.nonzero(distanceSqrdHalf<self.cutoff*self.cutoff)
        distanceSqrd = distanceSqrdHalf[indices]      # Ignoring the particles separated
        dr = drHalf[indices]                          # by a distance > cutoff
        return distanceSqrdAll, distanceSqrd, dr, indices
        
    @staticmethod
    def potentialEnergy(u, cutoff):
        """ Calculates the total potential energy, based on 
        the potential energies of all particles stored in the matrix
        u. Shifts the potential according to the cutoff.
        
        Parameters
        ----------
        u : ndarray
            array containing the potential energy of all the particles.
        cutoff : float
            cutoff distance: maximum length of the interactions. 3 by default.
            
        Returns
        -------
        float
            total potential energy
        """
        u[u == np.inf] = 0
        return 4 * (np.sum(u) - cutoff**(-12) - cutoff**(-6))
        
    def __call__(self, r):
        """ Lennard-Jones inter-atomic force. This is used in the
        integration loop to calculate the acceleration of particles. 
        
        Parameters
        ----------
        r : ndarray
            spatial coordinates at some timestep
            
        Returns
        -------
        ndarray
            the netto force acting on every particle
        float
            total potential energy
        ndarray
            current distance matrix
        """
        par, dim = r.shape
        
        # Compute force
        distanceSqrdAll, distanceSqrd, dr, indices = self.calculateDistanceMatrix(r)
        distancePowSixInv = np.nan_to_num(distanceSqrd**(-3))      # 1/r^6
        distancePowTwelveInv = distancePowSixInv**2                # 1/r^12
        factor = np.divide(2 * distancePowTwelveInv - distancePowSixInv, distanceSqrd)            # (2/r^12 - 1/r^6)/r^2
        factor[factor == np.inf] = 0
        force = 24 * np.einsum('i,ij->ij',factor,dr)
        
        # Ensure that force acts on the correct particles
        #forceMatrix = np.zeros((par,par,dim))
        upperTri = np.triu_indices(par, 1)
        #forceMatrix[upperTri] = -force
        #forceMatrix=forceMatrix.transpose(1,0,2)
        #forceMatrix[upperTri] = force

        a = np.arange(par*par).reshape(par,par)
        b = a[upperTri]
        c = b[indices]
        d = a.T
        e = d[upperTri]
        f = e[indices]
        force2 = np.zeros((par*par,dim))
        force2[c] = force
        force2[f] = -force
        force2 = force2.reshape(par,par,dim)
        force3 = np.sum(force2, axis=1)
        u = self.potentialEnergy(distancePowTwelveInv - distancePowSixInv, self.cutoff)
        return force3, u, distanceSqrdAll
