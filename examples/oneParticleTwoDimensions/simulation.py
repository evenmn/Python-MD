""" Example: A particle moving in two dimensions with reflective boundaries.
Initial position: (1,1)
Initial velocity: (1,1)
Length of box: 2
Total time: 10 ps
Time step: 0.01 ps
Potential: Lennard-Jones
Integrator: Forward-Euler

The position is plotted as a function of time, energy is not plotted
"""

from mdsolver import MDSolver
from mdsolver.potential import LennardJones
from mdsolver.integrator import ForwardEuler
from mdsolver.initpositions import SetPositions
from mdsolver.initvelocities import SetVelocities
from mdsolver.boundaryconditions import Reflective
from mdsolver.tasks import PlotPositions

# Simulate two particles in one dimension separated by a distance 1.5 sigma
solver = MDSolver(positions=SetPositions([[1.0, 1.0]]), 
                  velocities=SetVelocities([[1.0, 1.0]]),
                  boundaries=Reflective(lenbox=2), 
                  T=10, 
                  dt=0.01)
solver(potential=LennardJones(solver), 
       integrator=ForwardEuler(solver),
       tasks=[PlotPositions(solver)])
