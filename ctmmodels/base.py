import docplex.mp.model as cpx
import pandas as pd
import time
from ctmmodels.const import *

class BaseModel(object):
    sat_flow_rate       = 1 # vehicles / timestep
    flow_rate_reduction = 0.5 # Not specified in the paper
    g_min               = 6 # timesteps (change to 30 seconds)
    g_max               = 20 # timesteps (change to 120 seconds)
    time_step           = 1 # seconds / time step; NOT FROM PAPER
    time_range          = 60 # run for this many timesteps
    demand              = 600 # saturation
    flow_weight         = 0.2
    alpha               = 1
    model_name          = 'Thesis MILP Model'

    def __init__(self, sat_flow_rate=1, flow_rate_reduction=0.5, g_min=6,
                g_max=20, time_step=1, time_range=60, demand=600, flow_weight=0.2,
                alpha=1, model_name='Thesis MILP Model'):
        self.model_name = model_name
        self.model = cpx.Model(name=self.model_name)

        self.sat_flow_rate = sat_flow_rate
        self.flow_rate_reduction = flow_rate_reduction
        self.g_min = g_min
        self.g_max = g_max
        self.time_step = time_step
        self.time_range = time_range
        self.demand = demand
        self.flow_weight = flow_weight
        self.alpha = alpha

    def generate_sets(self):
        self.set_T = range(self.time_range)
        self.set_T_bounded = range(self.time_range-1)

        # Source cells: (0,approach_id)
        self.set_C_O = [(CELL_SOURCE,0,i)
            for i in range(APPROACHES)]

        # Sink cells: (0,approach_id)
        self.set_C_S = [(CELL_SINK,0,i)
            for i in range(APPROACHES)]

        # Movement cells: (movement_id, apporach_id)
        self.set_C_I = [(CELL_MOVEMENT,i,j)
            for i in range(MOVEMENT_CELLS)
            for j in range(APPROACHES)]

        # Normal cells: (cell_id, approach_id)
        self.set_C_N = [(CELL_NORMAL,i,j)
            for i in range(APPROACH_CELLS)
            for j in range(APPROACHES)]

        # Set of all cells: (cell_type, x, y)
        self.set_C = self.set_C_O + self.set_C_S + self.set_C_I + self.set_C_N
        self.set_C_labels = [
            'source',
            'sink',
            'movement',
            'normal'
        ]

        self.P = {i: P_mapping(i)
            for i in self.set_C}

        self.S = {i: S_mapping(i)
            for i in self.set_C}

        self.J = {i: J_mapping(i)
            for i in self.set_C_I}

    def generate_parameters(self):
        def M_mapping(i):
            if i in self.set_C_I:
                return (CELL_LENGTH / MEAN_CAR_LENGTH) * TURN_LANES[i[1]]
            elif i in self.set_C_O:
                return float("inf")
            return (CELL_LENGTH / MEAN_CAR_LENGTH) * APPROACH_LANES

        def F_mapping(i):
            if i in self.set_C_I:
                return self.sat_flow_rate * TURN_LANES[i[1]]
            return self.sat_flow_rate * APPROACH_LANES

        self.d = {(i,t): (float) (self.demand * APPROACH_LANES * self.time_step) / (3600)
            for i in self.set_C_O
            for t in self.set_T}

        self.M = {i: M_mapping(i)
            for i in self.set_C}

        self.F = {i: F_mapping(i)
            for i in self.set_C}

        self.r = {i: TURN_RATIOS[i[1]]
            for i in self.set_C_I}

    def reset_model(self):
        self.model = cpx.Model(name=self.model_name)

    def generate_decision_vars(self):
        self.g_vars = {(i,t): self.model.binary_var(
            name="g_{}^{}".format(i,t))
        for i in self.set_C_I
        for t in self.set_T}

        self.x_vars = {(i,t): self.model.continuous_var(
            lb=0,
            ub=self.M[i],
            name="x_{}^{}".format(i,t))
        for i in self.set_C
        for t in self.set_T}

        self.y_vars = {(i,j,t): self.model.continuous_var(
            lb=0,
            ub=min(self.F[i],self.F[j]),
            name="y_{}_{}^{}".format(i,j,t))
        for i in self.set_C
        for j in self.S[i]
        for t in self.set_T}

        self._g_count = len(self.g_vars)
        self._x_count = len(self.x_vars)
        self._y_count = len(self.y_vars)
        self._vars_count = self._g_count + self._x_count + self._y_count

    def generate_constraints(self):
        '''
        Only Constraints 0 to 3 will be created here; Constraints 4, 5, and 6 will be created in separate extensions
        '''

        init_src = [
            (self.model.add_constraint(
                ct=(
                    self.x_vars[(i,0)]
                    == self.d[(i,0)]
                ),
                ctname="init_src_{}".format(i)
            ))
            for i in self.set_C_O
        ]

        init_rest = [
            (self.model.add_constraint(
                ct=(
                    self.x_vars[(i,0)]
                    == 0
                ),
                ctname="init_rest_{}".format(i)
            ))
            for i in self.set_C if i not in self.set_C_O
        ]

        constraint_init = {
            'src': init_src
        }

        flowcon_1 = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.y_vars[(k,i,t)] for k in self.P[i])
                    - self.model.sum(self.y_vars[(i,j,t)] for j in self.S[i])
                    - self.x_vars[(i,t+1)]
                    + self.x_vars[(i,t)]
                    == 0
                ),
                ctname="flowcon_normal_{}^{}".format(i,t)
            ))
            for t in self.set_T_bounded
            for i in self.set_C_N + self.set_C_I
        ]

        flowcon_2 = [
            (self.model.add_constraint(
                ct=(
                    self.d[(i,t)]
                    - self.model.sum(self.y_vars[(i,j,t)] for j in self.S[i])
                    - self.x_vars[(i,t+1)]
                    + self.x_vars[(i,t)]
                    == 0
                ),
                ctname="flowcon_source_{}^{}".format(i,t)
            ))
            for t in self.set_T_bounded
            for i in self.set_C_O
        ]

        flowcon_3 = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.y_vars[(k,i,t)] for k in self.P[i])
                    - self.x_vars[(i,t+1)]
                    == 0
                ),
                ctname="flowcon_sink_{}^{}".format(i,t)
            ))
            for t in self.set_T_bounded
            for i in self.set_C_S
        ]

        constraint_flowcon = {
            'source': flowcon_2,
            'sink': flowcon_3,
            'rest': flowcon_1
        }

        flowrate_1 = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.y_vars[(i,j,t)] for j in self.S[i])
                    - self.x_vars[(i,t)]
                    <= 0
                ),
                ctname="flowrate_srccap_{}^{}".format(i,t)
            ))
            for t in self.set_T
            for i in self.set_C if i not in self.set_C_S
        ]

        flowrate_2 = [
            (self.model.add_constraint(
                ct=(
                    self.model.sum(self.y_vars[(i,j,t)] for i in self.P[j])
                    - self.M[j]
                    + self.x_vars[(j,t)]
                    <= 0
                ),
                ctname="flowrate_destcap_{}^{}".format(j,t)
            ))
            for t in self.set_T
            for j in self.set_C if j not in self.set_C_O
        ]

        constraint_flowrate = {
            'source_cap': flowrate_1,
            'sink_cap': flowrate_2
        }

        turnratios = [
            (self.model.add_constraint(
                ct=(
                    self.y_vars[(i,j,t)]
                    - self.model.sum(self.r[j] * self.y_vars[(i,k,t)] for k in self.S[i])
                    <= 0
                ),
                ctname="turnratios_{},{}^{}".format(i,j,t)
            ))
            for t in self.set_T
            for j in self.set_C_I
            for i in self.P[j]
        ]

        constraint_turnratios = {
            'turn_ratios': turnratios
        }

        self._constraints = {
            'init': constraint_init,
            'flowcon': constraint_flowcon,
            'flowrate': constraint_flowrate,
            'turnratios': constraint_turnratios,
        }

        self._constraints_count = 0

        for _, constraint_dict in self._constraints.iteritems():
            for _, constraint_array in constraint_dict.iteritems():
                self._constraints_count = self._constraints_count + len(constraint_array)
        
        return self._constraints_count

    def generate_objective_fxn(self):
        D_max = 1.0 / sum([ self.M[i] for i in self.set_C for t in self.set_T ])

        D_term = self.model.sum(
            self.model.sum(
                self.x_vars[(i,t)] - self.model.sum(
                    self.y_vars[(i,j,t)]
                    for j in self.S[i])
                for i in self.set_C)
            for t in self.set_T)

        F_term = self.model.sum(
                self.model.sum(
                    self.model.sum(
                        self.y_vars[(i,j,t)]
                    for j in self.S[i])
                for i in self.set_C if i not in self.set_C_S)
            for t in self.set_T)

        self._objective = self.alpha*D_term - self.flow_weight*F_term

        self.model.minimize(self._objective)
    
    def generate(self):
        self.generate_sets()
        self.generate_parameters()
        self.generate_decision_vars()
        self.generate_constraints()
        self.generate_objective_fxn()

    def solve(self, log_output=False):
        start = time.time()
        print("Solving...")
        self.model.solve(log_output=log_output)
        print("Done!")
        end = time.time()
        self._time = end - start
        print("Time elapsed: {}".format(self._time))
        return self._time

    def return_solution(self):
        df_x_raw = pd.DataFrame.from_dict(self.x_vars, orient="index", 
                                          columns = ["variable_object"])

        df_x_raw.reset_index(inplace=True)
        df_x_raw["volume"] = df_x_raw["variable_object"].apply(lambda item: item.solution_value)
        df_x_raw['cell'] = df_x_raw['index'].apply(lambda x: x[0])
        df_x_raw['timestep'] = df_x_raw['index'].apply(lambda x: x[1])

        df_x = df_x_raw[['timestep', 'cell', 'volume']]

        df_y_raw = pd.DataFrame.from_dict(self.y_vars, orient="index", 
                                          columns = ["variable_object"])

        df_y_raw.reset_index(inplace=True)
        df_y_raw["flow"] = df_y_raw["variable_object"].apply(lambda item: item.solution_value)
        df_y_raw['cell_from'] = df_y_raw['index'].apply(lambda x: x[0])
        df_y_raw['cell_to'] = df_y_raw['index'].apply(lambda x: x[1])
        df_y_raw['timestep'] = df_y_raw['index'].apply(lambda x: x[2])

        df_y = df_y_raw[['timestep', 'cell_from', 'cell_to', 'flow']]

        df_g_raw = pd.DataFrame.from_dict(self.g_vars, orient="index", 
                                          columns = ["variable_object"])

        df_g_raw.reset_index(inplace=True)
        df_g_raw["is_green"] = df_g_raw["variable_object"].apply(lambda item: item.solution_value)
        df_g_raw['cell'] = df_g_raw['index'].apply(lambda x: x[0])
        df_g_raw['timestep'] = df_g_raw['index'].apply(lambda x: x[1])

        df_g = df_g_raw[['timestep', 'cell', 'is_green']]
        
        return df_x, df_y, df_g