import docplex.mp.model as cpx
import pandas as pd
import time

from ctmmodels.const import *
from ctmmodels.base import BaseModel

class Constraint5Model(BaseModel):

    def __init__(self, *args, **kwargs):
        super(Constraint5Model, self).__init__(*args, **kwargs)
        
    def generate_constraint_5(self):
        green_flowrate = [
            (self.model.add_constraint(
                ct=(
                    self.y_vars[(i,j,t)]
                    - self.F[i]*self.g_vars[(i,t)]
                    <= 0
                ),
                ctname="green_flowrate_{},{}^{}".format(i,j,t)
            ))
            for t in self.set_T
            for i in self.set_C_I
            for j in self.S[i]
        ]

        slowstart_flowrate = [
            (self.model.add_constraint(
                ct=(
                    self.y_vars[(i,j,t+1)]
                    - self.F[i]
                    + (self.F[i]*self.flow_rate_reduction)*self.g_vars[(i,t+1)]
                    - (self.F[i]*self.flow_rate_reduction)*self.g_vars[(i,t)]
                    <= 0
                ),
                ctname="slowstart_flowrate_{},{}^{}".format(i,j,t+1)
            ))
            for t in self.set_T_bounded
            for i in self.set_C_I
            for j in self.S[i]
        ]

        self._constraints['greenflowrate'] = {
            'green_flowrate': green_flowrate,
            'slowstart_flowrate': slowstart_flowrate
        }

        self._constraints_count = self._constraints_count + len(green_flowrate) + len(slowstart_flowrate)

        green_max = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.g_vars[(i,z)] for z in range(t,t+self.g_max+2))
                    - self.g_max
                    <= 0
                ),
                ctname='green_max_{}^{}'.format(i,t)
            ))
            for t in range(self.time_range - self.g_max - 1)
            for i in self.set_C_I
        ]

        green_min = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.g_vars[(i,z)] for z in range(t+1,t+self.g_min+1))
                    - self.g_min*self.g_vars[(i,t+1)]
                    + self.g_min*self.g_vars[(i,t)]
                    >= 0
                ),
                ctname='green_min_{}^{}'.format(i,t)
            ))
            for t in range(self.time_range - self.g_min)
            for i in self.set_C_I
        ]

        self._constraints['greentime'] = {
            'green_max': green_max,
            'green_min': green_min
        }

        self._constraints_count = self._constraints_count + len(green_max) + len(green_min)

        return self._constraints_count

    def generate(self):
        super(Constraint5Model, self).generate()
        self.generate_constraint_5()