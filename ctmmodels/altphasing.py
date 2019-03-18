import docplex.mp.model as cpx
import pandas as pd
import time

from ctmmodels.const import *
from ctmmodels.base import BaseModel

class Constraint5AltPhasingModel(BaseModel):

    def __init__(self, *args, **kwargs):
        super(Constraint5AltPhasingModel, self).__init__(*args, **kwargs)
    
    def generate_sets(self):
        super(Constraint5AltPhasingModel, self).generate_sets()
        
        self.set_Phases = [(r, b, i) for r in range(2) for b in range(2) for i in range(2)]

        _tmp = CELL_MOVEMENT

        self.Phase_map = {
            (0,0,0): [(_tmp, LEFT_TURN, WESTBOUND), (_tmp, RIGHT_TURN, NORTHBOUND)], # WBL, NBR
            (0,0,1): [(_tmp, THROUGH_TURN, EASTBOUND), (_tmp, RIGHT_TURN, EASTBOUND)],
            (0,1,0): [(_tmp, LEFT_TURN, SOUTHBOUND), (_tmp, RIGHT_TURN, WESTBOUND)],
            (0,1,1): [(_tmp, THROUGH_TURN, SOUTHBOUND), (_tmp, RIGHT_TURN, SOUTHBOUND)],
            (1,0,0): [(_tmp, LEFT_TURN, EASTBOUND), (_tmp, RIGHT_TURN, SOUTHBOUND)],
            (1,0,1): [(_tmp, THROUGH_TURN, WESTBOUND), (_tmp, RIGHT_TURN, WESTBOUND)],
            (1,1,0): [(_tmp, LEFT_TURN, NORTHBOUND), (_tmp, RIGHT_TURN, EASTBOUND)],
            (1,1,1): [(_tmp, THROUGH_TURN, NORTHBOUND), (_tmp, RIGHT_TURN, NORTHBOUND)],
        }

    def generate_decision_vars(self):
        super(Constraint5AltPhasingModel, self).generate_decision_vars()

        self.g_vars = {(p,t): self.model.binary_var(
            name="g_{}^{}".format(p,t))
        for p in self.set_Phases
        for t in self.set_T}

        self._g_count = len(self.g_vars)
        self._vars_count = self._g_count + self._x_count + self._y_count

    def generate_constraints(self):
        super(Constraint5AltPhasingModel, self).generate_constraints()

        green_flowrate = [
            (self.model.add_constraint(
                ct=(
                    self.y_vars[(i,j,t)]
                    - self.F[i]*self.g_vars[(p,t)]
                    <= 0
                ),
                ctname="green_flowrate_{},{}^{}".format(i,j,t)
            ))
            for t in self.set_T
            for p in self.set_Phases
            for i in self.Phase_map[p]
            for j in self.S[i]
        ]

        slowstart_flowrate = [
            (self.model.add_constraint(
                ct=(
                    self.y_vars[(i,j,t+1)]
                    - self.F[i]
                    + (self.F[i]*self.flow_rate_reduction)*self.g_vars[(p,t+1)]
                    - (self.F[i]*self.flow_rate_reduction)*self.g_vars[(p,t)]
                    <= 0
                ),
                ctname="slowstart_flowrate_{},{}^{}".format(i,j,t+1)
            ))
            for t in self.set_T_bounded
            for p in self.set_Phases
            for i in self.Phase_map[p]
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
            for i in self.set_Phases
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
            for i in self.set_Phases
        ]

        self._constraints['greentime'] = {
            'green_max': green_max,
            'green_min': green_min
        }

        self._constraints_count = self._constraints_count + len(green_max) + len(green_min)

        return self._constraints_count

    def generate(self):
        self.generate_sets()
        self.generate_parameters()
        self.generate_decision_vars()
        self.generate_constraints()
        self.generate_objective_fxn()


class Constraint6AltPhasingModel(Constraint5AltPhasingModel):

    def __init__(self, *args, **kwargs):
        super(Constraint6Model, self).__init__(*args, **kwargs)
        
    def generate_constraint_6(self):
        movements_min = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.g_vars[(i,t)] for i in self.set_C_I)
                    >= 2
                ),
                ctname='movements_min^{}'.format(t)
            ))
            for t in self.set_T
        ]

        movements_max = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.g_vars[(i,t)] for i in self.set_C_I)
                    <= 4
                ),
                ctname='movements_max^{}'.format(t)
            ))
            for t in self.set_T
        ]

        movements_conflicting = [
            (self.model.add_constraint(
                ct=(
                    self.g_vars[(i,t)]
                    + self.g_vars[(j,t)]
                    <= 1
                ),
                ctname='movements_conflicting_{},{}^{}'.format(i,j,t)
            ))
            for t in self.set_T
            for i in self.set_C_I
            for j in self.J[i]
        ]

        self._constraints['conflicts'] = {
            'movements_min': movements_min,
            'movements_max': movements_max,
            'movements_conflicting': movements_conflicting
        }

        self._constraints_count = self._constraints_count + len(movements_min) + len(movements_max) + len(movements_conflicting)

        return self._constraints_count

    def generate(self):
        super(Constraint6Model, self).generate()
        self.generate_constraint_6()