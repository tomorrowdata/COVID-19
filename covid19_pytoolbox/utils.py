import numpy as np
import pandas as pd
from scipy import stats
import pprint
prettyprint = pprint.PrettyPrinter(indent=4)

from covid19_pytoolbox.modeling.Rt import naive
from covid19_pytoolbox.smoothing.seasonalRSVD.LogRSVD import LogSeasonalRegularizer


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


def cast_or_none(value, type_):
    if value is not None and type_ is not bool:
        return type_(value)

    if isinstance(value, str) and type_ is bool:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False

    return value

def RSVD_smooth_data_generic(df, filter_columns, alpha, beta, season_period=7, trend_alpha=100., difference_degree=2):

    initial_cols = df.columns

    prettyprint.pprint(filter_columns)

    for col in filter_columns:
        smoothcol = col+'_deseason'
        print(smoothcol)

        lrsvd = LogSeasonalRegularizer(
            df[col],
            season_period=season_period, max_r=season_period,
            trend_alpha=trend_alpha, difference_degree=difference_degree, verbose=True)

        m = lrsvd.fit()
        print(f'patterns: {m.final_r}')

        df[f'{smoothcol}'] = m.deseasoned
        df[f'{smoothcol}_seasonality'] = m.season_svd
        df[f'{smoothcol}_smoothed'] = m.trend
        df[f'{smoothcol}_residuals'] = m.residuals
        df[f'{smoothcol}_relative_residuals'] = m.relative_residuals

        df[f'{smoothcol}_smoothed_Rt'] = padnan(
            naive.compute_Rt(df[f'{smoothcol}_smoothed'].dropna(), alpha=alpha, beta=beta),
            (m.padding_left,0)
        )

        prettyprint.pprint(lrsvd.adfuller())

        print('new columns generated:')
        prettyprint.pprint([c for c in df.columns if c not in initial_cols])
