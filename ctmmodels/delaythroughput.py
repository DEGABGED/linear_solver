import docplex.mp.model as cpx
import pandas as pd
import time

from ctmmodels.const import *
from ctmmodels.altphasing import Constraint6AltPhasingModel


class DelayThroughputAltPhasing(Constraint6AltPhasingModel):

    def __init__(self, normalize=True, *args, **kwargs):
        super(Constraint5AltPhasingModel, self).__init__(*args, **kwargs)
        self.normalize = normalize

    def generate_objective_fxn(self):
        D_max = 1.0 / sum([ self.M[i] for i in self.set_C if i not in self.set_C_S for t in self.set_T ])

        T_max =  

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

        self._objective = self.alpha*D_term - (1 - self.alpha)*T_term

        self.model.minimize(self._objective)