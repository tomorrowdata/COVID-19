import os
import numpy as np
import pandas as pd

from covid19_pytoolbox.smoothing.seasonalRSVD import RSVD

def test():

    # load the data.retail.txt dataset used in the RSVD paper and supplementary material:
    path = os.path.dirname(RSVD.__file__)
    signal = pd.read_csv(
        os.path.join(path, 'data.retail.txt'),
        sep="\t", 
        names=['month','volume']
    )['volume']

    # apply the RSVD python porting to the retail dataset
    #  - the log is taken on the signal, as in the paper example
    rsvd = RSVD.SeasonalRegularizer(signal=np.log(signal), season_period=12, max_r=12)
    mfr = rsvd.fit()

    # load the reference seasonal component computed via original R-lang code published with the paper
    #  - the computation function is in the file func_RSVD_SA_SIM_NS.R
    ref_seasonal_trend = pd.read_csv(
        os.path.join(path, 'data.retail_ref_seasonal_component.csv')
    )['x']

    # check the computed and reference values are equals
    assert(np.allclose(mfr.season_svd, ref_seasonal_trend))

