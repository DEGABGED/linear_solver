import docplex.mp.model as cpx
import pandas as pd
import random

## Initialize sets, decision variables, parameters

# Constants from the parent paper
MOVEMENT_CELLS      = 3 # Number of movement cells per approach
APPROACH_CELLS      = 3 # Number of cells in each approach
APPROACHES          = 4 # Number of approaches per intersection
APPROACH_LANES      = 4 # Number of lanes per approach

FREE_FLOW_SPEED     = 44 # ft / s
CELL_LENGTH         = 88 # ft
SAT_FLOW_RATE       = 1 # vehicles / timestep
FLOW_RATE_REDUCTION = 0.5 # Not speciifed
G_MIN               = 6 # seconds
G_MAX               = 20 # seconds

FLOW_UNDERSAT       = 450 # veh / hr / lane
FLOW_SAT            = 900 
FLOW_OVERSAT        = 1800

TURN_RATIO_LEFT     = 0.1
TURN_RATIO_THROUGH  = 0.8
TURN_RATIO_RIGHT    = 0.1
TURN_RATIOS = [
    TURN_RATIO_LEFT,
    TURN_RATIO_THROUGH,
    TURN_RATIO_RIGHT
]

LEFT_TURN_LANES     = 1
RIGHT_TURN_LANES    = 1
THROUGH_TURN_LANES  = APPROACH_LANES - LEFT_TURN_LANES - RIGHT_TURN_LANES
if THROUGH_TURN_LANES <= 0:
    THROUGH_TURN_LANES = 1
TURN_LANES = [
    LEFT_TURN_LANES,
    THROUGH_TURN_LANES,
    RIGHT_TURN_LANES
]

TIME_STEP           = 1 # seconds / time step; NOT FROM PAPER
TIME_RANGE          = 60 # run for this many seconds

MEAN_CAR_LENGTH     = 15.8 # ft

# Sets
set_T = range(TIME_RANGE)
# Source cells: (0,approach_id)
set_C_O = [(0,0,i)
    for i in range(APPROACHES)]
# Sink cells: (0,approach_id)
set_C_S = [(1,0,i)
    for i in range(APPROACHES)]
# Movement cells: (movement_id, apporach_id)
set_C_I = [(2,i,j)
    for i in range(MOVEMENT_CELLS)
    for j in range(APPROACHES)]
# Normal cells: (cell_id, approach_id)
set_C_N = [(3,i,j)
    for i in range(APPROACH_CELLS)
    for j in range(APPROACHES)]
# Set of all cells: (cell_type, x, y)
set_C = set_C_O + set_C_S + set_C_I + set_C_N
set_C_labels = [
    'source',
    'sink',
    'movement',
    'normal'
]

# Parameters
def M_mapping(i):
    if i in set_C_I:
        return int(CELL_LENGTH / MEAN_CAR_LENGTH) * TURN_LANES[i[1]]
    return int(CELL_LENGTH / MEAN_CAR_LENGTH) * APPROACH_LANES 

def F_mapping(i):
    if i in set_C_I:
        return SAT_FLOW_RATE * TURN_LANES[i[1]]
    return SAT_FLOW_RATE * APPROACH_LANES

def P_mapping(i):
    pass

def S_mapping(i):
    return [(0,0,0)]

d = {(i,t): FLOW_SAT*APPROACH_LANES*TIME_STEP / (3600)
    for i in set_C_O
    for t in set_T}

M = {i: M_mapping(i)
    for i in set_C}

F = {i: F_mapping(i)
    for i in set_C}

r = {i: TURN_RATIOS[i[1]]
    for i in set_C_I}

alpha = 0.2

## Init model

model = cpx.Model(name="Thesis MILP model")

## Dictionary of decision variables

g_vars = {(i,t): model.binary_var(
    name="g_{}^{}".format(i,t))
for i in set_C_I
for t in set_T}

x_vars = {(i,t): model.continuous_var(
    lb=0,
    ub=M[i],
    name="x_{}^{}".format(i,t))
for i in set_C
for t in set_T}

y_vars = {(i,j,t): model.continuous_var(
    lb=0,
    ub=F[i],
    name="y_{}_{}^{}".format(i,j,t))
for i in set_C
for j in S_mapping(i)
for t in set_T}

## Dictionaries of constraints

## Objective Function

D_max = 1.0 / sum([ M[i] for i in set_C for t in set_T ])
T_max = 1.0 / sum([ M[i] for i in set_C_S for t in set_T ])

D = model.sum(
    model.sum(
        D_max * x_vars[(i,t)] - model.sum(
            D_max * y_vars[(i,j,t)]
            for j in S_mapping(i))
        for i in set_C)
    for t in set_T)

T = model.sum(
    model.sum(
        T_max * x_vars[(i,t)]
        for i in set_C_S)
    for t in set_T)


objective = alpha*D - (1-alpha)*T

model.minimize(objective)

## Solving

print("Solving...")
model.solve()
print("Done!")

## Results

opt_df = pd.DataFrame.from_dict(x_vars, orient="index", 
                                columns = ["variable_object"])

opt_df.reset_index(inplace=True)

opt_df["solution_value"] = opt_df["variable_object"].apply(lambda item: item.solution_value)

print(opt_df)
print(model.get_solve_details())
print(model.objective_value)