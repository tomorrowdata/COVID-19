import sys
sys.path.append('../')

import os
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error
import pymc3 as pm

from covid19_pytoolbox.settings import BASE_DATA_PATH, BASE_IMAGES_PATH
from covid19_pytoolbox.italy.data import DPC
from covid19_pytoolbox.modeling.datarevision.seasonal import draw_expanded_series, smooth_and_drop
from covid19_pytoolbox.modeling.Rt.bayesian import MCMC_sample
from covid19_pytoolbox.utils import smape, padnan

def save_MCMC_sampling(df, column, trace, pastdays, interval=0.95, start=0):
    interval_frac = int(interval*100)
    sampling_mean = np.mean(trace['r_t'], axis=0)

    df[f'{column}_Rt_MCMC_pastdays_{pastdays:03d}'] = padnan(sampling_mean, (start,pastdays))
    

    #credible interval
    sampling_hdi = pm.stats.hpd(trace['r_t'], hdi_prob=interval)
    df[f'{column}_Rt_MCMC_HDI_{interval_frac}_min_pastdays_{pastdays:03d}'] = padnan(
        sampling_hdi[:,0], (start,pastdays))
    df[f'{column}_Rt_MCMC_HDI_{interval_frac}_max_pastdays_{pastdays:03d}'] = padnan(
        sampling_hdi[:,1], (start,pastdays))


def compute_past_series(df, new_cases_col, pastdays_start, pastdays_end, draws, alpha, beta, trend_alpha, lower_ratio, upper_ratio, rt_col_prefix='smooth_deseas'):

    for pastdays in range(pastdays_start, pastdays_end-1,-1):
        print(f'\npastdays: {pastdays}')

        if pastdays == 0:
            sl = np.s_[:]
        else:
            sl = np.s_[:-pastdays]
            
        new_cases = df[new_cases_col].to_numpy()[sl]
        
        new_cases_expanded = draw_expanded_series(
                new_cases, draws=draws, season_period=7, trend_alpha=trend_alpha, difference_degree=2, 
                alpha=alpha, beta=beta, method='residuals',
                truncate=False
            )
        
        print('pre smooth_and_drop')
        print(f'new_cases_expanded.shape: {new_cases_expanded.shape}')
        
        new_cases_smoothed, rel_eps, padding_left = smooth_and_drop(
            new_cases_expanded, season_period=7, trend_alpha=100.,difference_degree=2)

        print('post smooth_and_drop')
        print(f'new_cases_smoothed.shape: {new_cases_smoothed.shape}')
        print(f'rel_eps.shape: {rel_eps.shape}')    
        print(f'padding_left: {padding_left}')
            
        simulations = []
        for new_cases_s, rel_eps_s in zip(new_cases_smoothed, rel_eps):
            print(f'new_cases_s cut left: {new_cases_s[~np.isnan(new_cases_s)].shape}')
            print(f'rel_eps_s cut left: {rel_eps_s[~np.isnan(rel_eps_s)].shape}')
            
            try:
                model_, trace_ = MCMC_sample(
                    onset=new_cases_s[~np.isnan(new_cases_s)],
                    alpha=alpha, beta=beta,
                    rel_eps=rel_eps_s[~np.isnan(rel_eps_s)],
                    start=0, window=None,
                    chains=4,
                    tune=500,
                    draws=500,
                    cores=4,
                    dry=False,
                    progressbar=False
                )
                simulations.append(trace_)
            except Exception as ex:
                print(ex)
                print(f'skipping pastdays {pastdays:03d}')

        sampled_Rt = np.array([t['r_t'] for t in simulations])
        combined_trace = {'r_t': sampled_Rt.reshape((-1,sampled_Rt.shape[2]))}

        save_MCMC_sampling(
            df, f'{new_cases_col}_{rt_col_prefix}', combined_trace, pastdays, interval=0.95, start=padding_left+1)

        
        df.to_pickle(os.path.join(BASE_DATA_PATH,
            f'computed/WIP/deseason_MCMC_Rt_pastdays_{pastdays_start:03d}_{pastdays_end:03d}.pickle'))    

def main(pastdays_start, pastdays_end):

    print(f'pastdays_start: {pastdays_start} - pastdays_end: {pastdays_end}')

    alpha = 1.87
    beta = 0.28

    ALPHA=100.

    DPC_data = DPC.load_daily_cases_from_github()

    compute_past_series(
        DPC_data, 'nuovi_positivi', 
        pastdays_start=pastdays_start, pastdays_end=pastdays_end, draws=10,
        alpha=alpha, beta=beta, trend_alpha=ALPHA, lower_ratio=0.5, upper_ratio=1.5)

if __name__ == "__main__":
    main(*map(int, sys.argv[1:]))
