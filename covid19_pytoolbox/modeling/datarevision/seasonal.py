import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error

from covid19_pytoolbox.smoothing.seasonalRSVD.LogRSVD import LogSeasonalRegularizer
from covid19_pytoolbox.smoothing.tikhonovreg import TikhonovRegularization
from covid19_pytoolbox.modeling import Rt
from covid19_pytoolbox.utils import smape, padnan


def next_from_taylor(x):
    return 2.5*x - 2.*padnan(x[:-1],(1,0)) + 0.5*padnan(x[:-2],(2,0))

def predict_next_case(cases, rt, alpha, beta):
    return (
        Rt.naive.infectious_charge(np.nan_to_num(padnan(cases,(0,1)),nan=0.), alpha=alpha,beta=beta)[1:] 
        * next_from_taylor(rt)
    )

def taylor_pred_errors(cases, cases_pred):
    args_rt = cases.dropna()[4:], cases_pred.dropna()
    args_dummy = cases.dropna()[1:], cases[:-1].dropna()
    return{
        'pred_with_rt': {
            'smape': smape(*args_rt)*100,
            'rmse': mean_squared_error(*args_rt, squared=False)            
        },
        'pred_dummy': {
            'smape': smape(*args_dummy)*100,
            'rmse': mean_squared_error(*args_dummy, squared=False)                        
        }
    }

def predict_next_value(X, use_last_values=None, search_steps=100):
    if not use_last_values:
        use_last_values = X.shape[0]
        
    search_alpha = np.linspace(0,10.,search_steps)
    pad = 3

    smapes = []
    x = X[-use_last_values:]
    for alpha in search_alpha:
        tik = TikhonovRegularization(timesteps=len(x), alpha=alpha)
        x_tik = tik.stat_smooth_data(x, verbose=False)
        x_pred = padnan(next_from_taylor(x_tik), (1,0))
        pred_smape = smape(x[pad:],x_pred[pad:-1])*100
        smapes.append(pred_smape)

    alpha = search_alpha[np.argmin(smapes)]
    tik = TikhonovRegularization(timesteps=len(x), alpha=alpha)
    x_tik = tik.stat_smooth_data(x, verbose=False)
    x_pred = padnan(next_from_taylor(x_tik), (X.shape[0] - use_last_values + 1,0))
    return x_pred

def draw_expanded_series(X, draws, season_period, trend_alpha, difference_degree, truncate, alpha, beta, verbose=False):

    if type(X) == pd.Series:
        X = X.to_numpy()
        
    # deseason:
    lrsvd = LogSeasonalRegularizer(
        X, season_period=season_period, max_r=season_period, 
        trend_alpha=trend_alpha, difference_degree=difference_degree, verbose=verbose)    
    m = lrsvd.fit()
    
    # truncate means that, AFTER deseasoning, we drop the last element:
    # in this way, deseasoning is affected by the additional element in 
    # the original series, while we drop the last result as it is in the future
    if truncate:
        sl = np.s_[:-1]
    else:
        sl = np.s_[:]
    T, S, eps_rel = m.trend[sl], m.season_svd[sl], m.relative_residuals[sl]
    
    _, _, S_hat = LogSeasonalRegularizer.periods_to_matrix(S, season_period)
    #print(S_hat[-2:,:])
    
    # compute Rt on T
    rt = padnan(Rt.naive.compute_Rt(T[m.padding_left:], alpha, beta), (m.padding_left,0))
    
    # predict next T value
    T_next = predict_next_case(T, rt, alpha, beta)[-1]
    
    # predict next S value
    # we need the season of tomorrow
    # the season of today is the last column in S_hat
    # hence -> the season of tomorrow is the first column, as seasons are periodic
    S_tomorrow = S_hat[:,0]
    # predict the next value of S_tomorrow
    S_tomorrow_next = predict_next_value(S_tomorrow, use_last_values=15)[-1]
        
    # compute the next X value
    lower, upper = T_next*0.8, T_next*1.2
    mu, sigma = T_next, T_next
    possible_T_next = stats.truncnorm(
        (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
    X_next = S_tomorrow_next + possible_T_next.rvs((draws,1))
    
    # expand the original X series and return it
    X_expanded = np.repeat(X[sl].reshape((1,-1)), draws, axis=0)
    X_expanded = np.append(X_expanded, X_next, axis=1)
    
    return X_expanded

def smooth_and_drop(X, season_period, trend_alpha, difference_degree, verbose=False):
    smoothed = []
    smoothed_rel_eps = []
    
    for x in X:
        lrsvd = LogSeasonalRegularizer(
            x, season_period=season_period, max_r=season_period, 
            trend_alpha=trend_alpha, difference_degree=difference_degree, verbose=verbose)    
        m = lrsvd.fit()
        
        smoothed.append(m.trend[:-1])
        smoothed_rel_eps.append(m.relative_residuals[:-1])
    
    lT = len(smoothed[0])
    return np.array(smoothed).reshape(-1,lT), np.array(smoothed_rel_eps).reshape(-1,lT), m.padding_left
