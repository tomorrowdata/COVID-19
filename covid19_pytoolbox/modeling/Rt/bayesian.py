import numpy as np
import pandas as pd

import arviz as az
import pymc3 as pm
import theano.tensor as tt
import theano

from covid19_pytoolbox.modeling import Rt

def MCMC_sample(
    onset, 
    alpha, 
    beta, 
    rel_eps=None,
    eps_window=7,
    imported_ratio=None,
    imported_ratio_window=14,
    start=0, window=None, 
    chains=1, tune=4000, draws=4000, 
    target_accept=0.95, 
    max_treedepth=10,
    dry=False, 
    cores=None,
    progressbar=True
):

    if not window:
        window = len(onset)
        
    if type(onset)==pd.DataFrame:
        onset = onset.values
        
    onset_ = onset[start:start+window]

    # we fill nans created by the rolling std with small fixed values
    # as pymc can't draw samples from 0. standard deviation
    # this is going to affect only the very beginning of the series, which we are not interested into
    fill_std = 10.**(-3)
    fill_mean = 0.

    if not rel_eps is None:
        rel_eps_ = rel_eps[start:start+window]
        rel_eps_mean = pd.Series(rel_eps_).rolling(window=eps_window).mean().fillna(fill_mean).to_numpy()
        rel_eps_std = pd.Series(rel_eps_).rolling(window=eps_window).std().fillna(fill_std).to_numpy()
    
    if not imported_ratio is None:
        imported_ratio_ = imported_ratio[start:start+window]

        # fill last missing values of mean and std forwarding the last available value
        # as imported data are available with 7-14 days delay
        imported_ratio_mean = pd.Series(imported_ratio_).rolling(window=imported_ratio_window, min_periods=1).mean().fillna(method='ffill').to_numpy()
        imported_ratio_std = pd.Series(imported_ratio_).rolling(window=imported_ratio_window, min_periods=1).std().fillna(method='ffill').to_numpy()


    steps = len(onset_)
    x = np.linspace(1,steps-1, steps)
    w = Rt.naive.gamma_df(x, alpha, beta)    
    
    with pm.Model() as model:
                
        # draws R_t from a prior normal distribution
        r_t = pm.Normal("r_t", mu=1.3, sigma=10., shape=len(onset_)-1)

        if not rel_eps is None:
            # sample noise from deseason epsilons and add it to the onsets
            rel_residuals = pm.Normal(
                name="rel_residuals", 
                mu=rel_eps_mean, 
                sigma=rel_eps_std,
                shape=len(rel_eps_std)
            )
            onset_residuals = pm.Deterministic(
                "onset_residuals", 
                onset_ + onset_ * rel_residuals
            )
        else:
            onset_residuals = onset_
        
        # compute the exptected number of current infectious 
        # based on the sampled R_t and the know past values of infectious
        
        # this is the Theano implementation of the function in 
        # modeling.Rt.naive.infectious_charge
        infectious_charge_ = pm.Deterministic(
            "infectious_charge",
            tt.as_tensor([
                tt.sum(onset_residuals[t-1::-1]*w[:t]) 
                for t in range(1, steps)        
            ])            
        )         

        # estimate the expected today based on Rt esimate
        expected_today = r_t * infectious_charge_

        # correct the estimate based on the imported cases
        if not imported_ratio is None:
            # correct the onsets by reducing of the number of imported cases
            # sample imported ratios and correct to the onsets_residuals
            
            imported_ratio_correction = pm.TruncatedNormal(
                name="imported_ratios_", 
                mu=imported_ratio_mean, 
                sigma=imported_ratio_std,
                lower= 0.,
                upper=1.,
                shape=len(imported_ratio_std)
            )
            expected_today_corrected = expected_today * (1. - imported_ratio_correction)
        else:
            expected_today_corrected = expected_today
        
        # Poisson requirements
        mu = pm.math.maximum(.1, expected_today)        
        observed = (expected_today_corrected[1:]).round()

        # test the posterior: 
        # mu values derived from R_t samples 
        # must converge to the mean of real cases 
        # if they are Poisson distributed, as they are
        cases = pm.Poisson('cases', mu=mu, observed=observed)

        trace = None
        if not dry:
            trace = pm.sample(
                chains=chains,
                cores=cores,
                tune=tune,
                draws=draws,
                target_accept=target_accept, max_treedepth=max_treedepth,
                progressbar=progressbar)
            
    return model, trace