import numpy as np
from scipy import stats

def gamma_df(x, alpha, beta):
    return stats.gamma.pdf(x, a=alpha, scale=1/beta)

def gamma_pf(x, alpha, beta):
    return stats.gamma.ppf(x, a=alpha, scale=1/beta)

def infectious_charge(series, alpha, beta):
    steps = len(series)
    x = np.linspace(1,steps-1, steps)
    w = gamma_df(x, alpha, beta)
    
    infectious_charge_ = [np.nan] + [
        sum(series[t-1::-1]*w[:t]) 
        for t in range(1, steps)        
    ]
    
    return np.asarray(infectious_charge_)

def compute_naive_Rt(series, alpha, beta):
    infectious_charge_ = infectious_charge(series, alpha, beta)
    
    return series / infectious_charge_