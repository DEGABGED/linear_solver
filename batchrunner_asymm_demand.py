import os
import numpy as np
import pandas as pd

from batchrunners.const import *
from batchrunners.generators.dataframe import DataframeGenerator
from batchrunners.generators.graphs import GraphGenerator


dg = DataframeGenerator(
    df_path=os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'dataframes'
    )
)

# Try and run on a much smaller simplex first

#dg.run_on_simplex((450,900), simplex_slice=generate_simplex(4), folder='batchrunner_test')

gg = GraphGenerator(
    image_path=os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'graphs'
    ),
    simplex_range=10,
    folder='asymm_demand'
)

df = pd.read_pickle("dataframes/asymm_demand/results_simplex_d(450, 900).pkl")
gg.plot_obj_values(df, "Asymmetric demand (450, 900)", filename_partial='450_900_demand')