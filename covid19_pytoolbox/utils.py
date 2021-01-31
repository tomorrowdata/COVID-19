import numpy as np

def padnan(a, paddings, value=np.nan):
    return np.pad(a, paddings, mode='constant', constant_values=(value, value))

def smape(A, F):
    if type(A) == pd.Series:
        A = A.to_numpy()
    if type(F) == pd.Series:
        F = F.to_numpy()
        
    return 1/len(A) * np.sum(2 * np.abs(F - A) / (np.abs(A) + np.abs(F)))