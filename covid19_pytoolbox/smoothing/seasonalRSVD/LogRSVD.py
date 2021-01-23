from collections import namedtuple
import numpy as np

from covid19_pytoolbox.smoothing.seasonalRSVD.RSVD import SeasonalRegularizer

class LogSeasonalRegularizer(SeasonalRegularizer):

    def __init__(self, signal, season_period, max_r, trend_alpha, difference_degree, verbose=False):

        signal = np.log(signal)

        super().__init__(signal, season_period, max_r, trend_alpha, difference_degree, verbose)

    
    def fit(self):
        m = super().fit()

        deseasoned = np.exp(m.deseasoned)        
        season_svd = deseasoned * (np.exp(m.season_svd) - 1.)

        trend = np.exp(m.trend)

        # residuals:
        relative_residuals = np.exp(m.residuals) -1
        residuals = trend * relative_residuals

        multifitresult = namedtuple('multifitlogresult', [
            'info_cri', 'u_hat', 'v_fixed', 'v_hat2', 'season_svd', 
            'final_r', 'padding_left',
            'deseasoned', 'trend', 'residuals', 'relative_residuals'
        ])

        return multifitresult(
            *m[:-6],
            season_svd, m.final_r, m.padding_left,
            deseasoned, trend, residuals, relative_residuals
        )
