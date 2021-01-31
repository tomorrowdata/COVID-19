from collections import namedtuple
import numpy as np
import pandas as pd

from covid19_pytoolbox.smoothing.seasonalRSVD.RSVD import SeasonalRegularizer

class LogSeasonalRegularizer(SeasonalRegularizer):

    def __init__(self, signal, season_period, max_r, trend_alpha, difference_degree, verbose=False):

        if type(signal) == pd.Series:
            signal = signal.to_numpy()
        
        # fix cases when log is not defined
        # as we are dealing with volumes, 1 is ok instead of 0
        signal[signal<=0.]=1.

        signal = np.log(signal)

        super().__init__(signal, season_period, max_r, trend_alpha, difference_degree, verbose)

    
    def fit(self):
        m = super().fit()

        deseasoned = np.exp(m.deseasoned)        
        season_svd = deseasoned * (np.exp(m.season_svd) - 1.)
        seasons = season_svd[self.padding_left:]
        season_hat = seasons.reshape(-1, self.season_period)

        trend = np.exp(m.trend)

        # residuals:
        relative_residuals = np.exp(m.residuals) -1
        residuals = trend * relative_residuals

        multifitresult = namedtuple('multifitlogresult', [
            'info_cri', 'u_hat', 'v_fixed', 'v_hat2', 'season_svd', 'season_hat',
            'final_r', 'padding_left',
            'deseasoned', 'trend', 'residuals', 'relative_residuals'
        ])

        return multifitresult(
            *m[:-7],
            season_svd, season_hat, m.final_r, m.padding_left,
            deseasoned, trend, residuals, relative_residuals
        )
