import os
import numpy as np
import pandas as pd

from batchrunners.const import *
from ctmmodels.const import *
from ctmmodels.delaythroughput import DelayThroughputSimplex as Model


class DataframeGenerator(object):

    def __init__(self, parameters=DEFAULT_PARAMETERS, time_range=TIME_RANGE, df_path=DF_PATH):
        self.time_range = TIME_RANGE

        self.parameters = parameters
        self.parameters['time_range'] = TIME_RANGE
        self.df_path = df_path

    def run_model(self, demand, alpha=1, beta=0, gamma=0, log_output=True):
        model = Model(
            demand=demand,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            **self.parameters
        )
        model.generate()
        runtime = model.solve(log_output=log_output)

        dfx, dfy, dfg = model.return_solution()
        dfparams = model.return_parameters()
        obj_values = model.return_objective_value()

        misc = {}
        misc['capacity'] = dfparams.capacity[(3,0,1)]
        misc['maxflow'] = dfparams.max_flow[(3,0,1)]
        misc['runtime'] = runtime
        misc['delay'] = obj_values[0]
        misc['throughput'] = obj_values[1]
        misc['obj_value'] = obj_values[2]
        
        return dfx, dfy, dfg, misc

    def save_df(self, df, filename):
        df.to_pickle(filename + ".pkl")

    def run_on_simplex(self, demand, simplex_slice=generate_simplex(10), log_output=False, folder='simplex', parameters=None, save_decision_variables=False, varying_label=None):
        '''
        Runs the model on a 3-simplex, across a set of parameters.
        By default, the varying parameter is demand.
        '''

        if parameters is None:
            parameters = self.parameters
        if varying_label is None:
            varying_label = "d{}".format(demand)

        _df_tuples = []
        _path = os.path.join(self.df_path, folder)
    
        for p in simplex_slice:
            a, b, c = p
            dfx, dfy, dfg, misc = self.run_model(demand=demand, alpha=a, beta=b, gamma=c, log_output=log_output)
            _df_tuples.append((demand, misc['runtime'], misc['delay'], misc['throughput'], misc['obj_value'], a, b, c))

            if save_decision_variables:
                self.save_df(dfx, "{}/volumes/volumes_{}_a{}_b{}_c{}".format(_path, varying_label, a, b, c))
                self.save_df(dfy, "{}/flows/flows_{}_a{}_b{}_c{}".format(_path, varying_label, a, b, c))

            self.save_df(dfg, "{}/greentimes/greentimes_{}_a{}_b{}_c{}".format(_path, varying_label, a, b, c))

            print("Done with point ({}, {}, {})!\n".format(a, b, c))
        
        df = pd.DataFrame(data=_df_tuples,columns=['demand', 'runtime', 'delay', 'throughput', 'objective_value', 'alpha', 'beta', 'gamma'])
        self.save_df(df, "{}/results_simplex_{}".format(_path, varying_label))

    def test_package(self):
        print("Hello!")
        print(self.parameters)
