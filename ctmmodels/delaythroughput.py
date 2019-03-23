import docplex.mp.model as cpx
import pandas as pd
import time
from math import log10

from ctmmodels.const import *
from ctmmodels.nophasing import Constraint6Model
from ctmmodels.altphasing import Constraint6AltPhasingModel


class DelayThroughput(Constraint6Model):

    def __init__(self, normalize=True, *args, **kwargs):
        super(Constraint6Model, self).__init__(*args, **kwargs)
        self.normalize = normalize

    def generate_objective_fxn(self):
        # Capacities in all but the source and sink cells are full during maximum delay
        D_max = sum([ self.M[i] for i in self.set_C if i not in self.set_C_S + self.set_C_O for t in self.set_T ])

        # The volume in the source cell increases by the demand for each timestep
        D_max = D_max + sum([ self.d[(i,t)] for i in self.set_C_O for t in self.set_T ])

        # The volume in the sink cell indicates the throughput of the intersection
        T_max =  sum([ self.M[i] for i in self.set_C_S for t in self.set_T ])

        # To prevent loss of precision, we can scale up normalized results by the magnitude of the larger of the 2 values
        scale = 10**int(log10(max(D_max, T_max)))
        
        D_term = self.model.sum(
            self.model.sum(
                self.x_vars[(i,t)] - self.model.sum(
                    self.y_vars[(i,j,t)]
                    for j in self.S[i])
                for i in self.set_C if i not in self.set_C_S)
            for t in self.set_T)

        T_term = self.model.sum(
            self.model.sum(
                self.x_vars[(i,t)]
                for i in self.set_C_S)
            for t in self.set_T)

        if (self.normalize):
            self._objective = (self.alpha)*(D_term * scale / D_max) - (1 - self.alpha)*(T_term * scale / T_max)
        else:
            self._objective = (self.alpha)*D_term - (1 - self.alpha)*T_term

        self.model.minimize(self._objective)

    def generate(self):
        self.generate_sets()
        self.generate_parameters()
        self.generate_decision_vars()
        self.generate_constraints()
        self.generate_objective_fxn()


class DelayThroughputAltPhasing(Constraint6AltPhasingModel):

    def __init__(self, normalize=True, *args, **kwargs):
        super(Constraint6AltPhasingModel, self).__init__(*args, **kwargs)
        self.normalize = normalize

    def generate_objective_fxn(self):
        # Capacities in all but the source and sink cells are full during maximum delay
        D_max = sum([ self.M[i] for i in self.set_C if i not in self.set_C_S + self.set_C_O for t in self.set_T ])

        # The volume in the source cell increases by the demand for each timestep
        D_max = D_max + sum([ self.d[(i,t)] for i in self.set_C_O for t in self.set_T ])

        # The volume in the sink cell indicates the throughput of the intersection
        T_max =  sum([ self.M[i] for i in self.set_C_S for t in self.set_T ])

        # To prevent loss of precision, we can scale up normalized results by the magnitude of the larger of the 2 values
        scale = 10**int(log10(max(D_max, T_max)))
        
        D_term = self.model.sum(
            self.model.sum(
                self.x_vars[(i,t)] - self.model.sum(
                    self.y_vars[(i,j,t)]
                    for j in self.S[i])
                for i in self.set_C if i not in self.set_C_S)
            for t in self.set_T)

        T_term = self.model.sum(
            self.model.sum(
                self.x_vars[(i,t)]
                for i in self.set_C_S)
            for t in self.set_T)

        if (self.normalize):
            self._objective = (self.alpha)*(D_term * scale / D_max) - (1 - self.alpha)*(T_term * scale / T_max)
        else:
            self._objective = (self.alpha)*D_term - (1 - self.alpha)*T_term

        self.model.minimize(self._objective)

    def generate(self):
        self.generate_sets()
        self.generate_parameters()
        self.generate_decision_vars()
        self.generate_constraints()
        self.generate_objective_fxn()
    