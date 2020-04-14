import numpy as np
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning) 

class MDSolver:
    """ Initialize the MDSolver class. This includes defining the
    time scales, initialize positions and velocities, and define
    matplotlib fixes.
    
    Parameters
    ----------
    positions : obj
        class object defined by initpositions.py. Face-centered cube
        with length 3 and 4 particles as default.
    velocity : obj
        class object defined by initvelocities.py. No velocity as default.
    boundaries : obj
        class object defined by boundaryconditions.py. Open boundaries 
        as default.
    T : float
        total time
    dt : float
        time step
    """
    
    from mdsolver.initpositions import FCC
    from mdsolver.initvelocities import Zero
    from mdsolver.boundaryconditions import Open
    
    def __init__(self, positions=FCC(cells=1, lenbulk=3), 
                       velocities=Zero(), 
                       boundaries=Open(),
                       T=5, 
                       dt=0.01):
        
        self.boundaries = boundaries
        from collections import namedtuple
        self.State = namedtuple('State', ['r', 'v', 'a', 'u', 'd', 'c'])
        
        # Define time scale and number of steps
        self.T = T
        self.dt = dt
        self.N = int(T/dt)
        self.time = np.linspace(0, T, self.N)
        
        # Initialize positions
        self.r0 = positions()
        self.numparticles, self.numdimensions = self.r0.shape
        
        # Initialize velocities
        self.v0 = velocities(self.numparticles, self.numdimensions)
        
        # print to terminal
        self.print_to_terminal()
        
        
    def __repr__(self):
        return """MDSolver is the heart of the molecular dynamics code. 
                  It sets up the solver and distribute tasks to other 
                  classes. """
        
    def print_to_terminal(self):
        """ Print information to terminal
        """
        print("\n\n" + 14 * "=", " SYSTEM INFORMATION ", 14 * "=")
        print("Number of particles:  ", self.numparticles)
        print("Number of dimensions: ", self.numdimensions)
        print("Boundary conditions:  ", self.boundaries)
        print("Total time:           ", self.T, "\tps")
        print("Timestep:             ", self.dt, "\tps")
        print(50 * "=" + "\n\n")
        
        
    @staticmethod    
    def print_simulation(potential, integrator, tasks):
        """ Print information to terminal when starting a simulation
        
        Parameters
        ----------
        potential : obj
            object defining the inter-atomic potential
        integrator : obj
            object defining the integrator
        """
        print("\n\n" + 12 * "=", " SIMULATION INFORMATION ", 12 * "=")
        print("Potential:            ", potential)
        print("Integrator:           ", integrator)
        for task in tasks:
            print(task)
        print(50 * "=" + "\n\n")
        
    
    def __call__(self, potential, 
                       integrator,
                       tasks): 
        """ Integration loop. Computes the time-development of position and 
        velocity using a given integrator and inter-atomic potential.
        
        Parameters
        ----------
        potential : obj
            object defining the inter-atomic potential
        integrator : obj
            object defining the integrator
        """
        self.potential = potential
        
        self.print_simulation(potential, integrator, tasks)
        
        # Initialize    
        a, uDecomp, dSqrd = potential(self.r0)
        state = self.State(r=self.r0, v=self.v0, a=a, u=uDecomp, d=dSqrd, c=0)
            
        for task in tasks:
            task._update(state, 0)
            
        # Integration loop
        from tqdm import tqdm
        for t in tqdm(range(self.N)):   # Integration loop
            state = integrator(state)
            for task in tasks:
                task._update(state, t)
                
        # Perform tasks
        for task in tasks:
            task()


if __name__ == "__main__":
    # EXAMPLE: TWO PARTICLES IN ONE DIMENSION INITIALLY SEPARATED BY 1.5 SIGMA
    from potential import LennardJones
    from integrator import EulerChromer
    from initpositions import SetPositions
    from tasks import PlotEnergy, DumpPositions, PlotDistance

    solver = MDSolver(positions=SetPositions([[0.0], [1.5]]), 
                      T=5, 
                      dt=0.01)
    solver(potential=LennardJones(solver), 
           integrator=EulerChromer(solver),
           tasks=[PlotEnergy(solver),
                  DumpPositions(solver, "2N_1D_1.5S.data"),
                  PlotDistance(solver)])
