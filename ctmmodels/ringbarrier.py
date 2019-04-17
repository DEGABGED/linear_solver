import docplex.mp.model as cpx
import pandas as pd
import time
from math import log10

from ctmmodels.const import *
from ctmmodels.delaythroughput import DelayThroughputSimplex

class RingBarrier(DelayThroughputSimplex):

    def __init__(self, *args, **kwargs):
        super(DelayThroughputSimplex, self).__init__(*args, **kwargs)

    def generate_constraints(self):

