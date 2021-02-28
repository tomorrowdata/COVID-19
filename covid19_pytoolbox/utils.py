import numpy as np
import pandas as pd
from scipy import stats

def padnan(a, paddings, value=np.nan):
    return np.pad(a, paddings, mode='constant', constant_values=(value, value))

def smape(A, F):
    if type(A) == pd.Series:
        A = A.to_numpy()
    if type(F) == pd.Series:
        F = F.to_numpy()
        
    return 1/len(A) * np.sum(2 * np.abs(F - A) / (np.abs(A) + np.abs(F)))

def truncnorm(mu, sigma, lower, upper, size):
    tn = stats.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
    return tn.rvs(size)