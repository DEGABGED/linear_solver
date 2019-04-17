import os
import sys

from batchrunners.generators.dataframe import DataframeGenerator

def run_test_case(demand1, demand2):
    demand = (demand1, demand2)
    dg = DataframeGenerator(
        df_path=os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'dataframes'
        )
    )
    dg.run_on_simplex(demand, folder='asymm_demand')

def main():
    run_test_case(int(sys.argv[1]), int(sys.argv[2]))

if __name__ == "__main__":
    main()
