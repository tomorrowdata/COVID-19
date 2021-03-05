import os
import pprint
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from covid19_pytoolbox.modeling.Rt import naive
from covid19_pytoolbox.smoothing.seasonalRSVD.LogRSVD import LogSeasonalRegularizer
from covid19_pytoolbox.utils import smape, padnan


prettyprint = pprint.PrettyPrinter(indent=4)

def load_daily_cases_from_pub_api():

    df = pd.read_csv(
        'https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&metric=cumCasesByPublishDate&metric=newCasesByPublishDate&metric=transmissionRateMin&metric=transmissionRateMax&format=csv',
        parse_dates=['date'],
        #date_parser=parse_date
    )

    df.sort_values(by='date', inplace=True)
    df.reset_index(inplace=True, drop=True)    
    
    return df

def preprocess(df):

    df['cumCasesByPublishDateRestored'] = df['newCasesByPublishDate'].cumsum()

    delay = 15
    df['transmissionRateMin_shifted'] = df['transmissionRateMin'].shift(-delay)
    df['transmissionRateMax_shifted'] = df['transmissionRateMax'].shift(-delay)
    df['transmissionRateMinErr_shifted'] = (df['transmissionRateMax_shifted']-df['transmissionRateMin_shifted'])/2.
    df['transmissionRateMaxErr_shifted'] = df['transmissionRateMinErr_shifted']
    df['transmissionRateAvg_shifted'] = df['transmissionRateMin_shifted']+df['transmissionRateMinErr_shifted']
    df['transmissionRateTimeRangeMin'] = df['date'].dt.normalize()+timedelta(days=-3, hours=-12)
    df['transmissionRateTimeRangeMax'] = df['date'].dt.normalize()+timedelta(days=+3, hours=+12)

    TIMESTEPS = len(df.cumCasesByPublishDate)

    return TIMESTEPS

def compute_first_diffs(df):

    def first_diff(df, col):
        return (df[col] - df[col].shift(1)).fillna(0)

    cols = {
    }

    prettyprint.pprint(cols)


    for diffcol, col in cols.items():
        df[diffcol] = first_diff(df, col)


def tikhonov_smooth_differentiate(df, regularizer):

    cols = {
        'newCasesByPublishDate_smoothed': 'cumCasesByPublishDateRestored',
    }

    prettyprint.pprint(cols)

    for smoothcol, col in cols.items():
        print(smoothcol, end=' - ')
        df[smoothcol] = regularizer.stat_smooth_differentiate(df[col])

def bulk_compute_naive_Rt(df, alpha, beta):

    rt_on_fields = [
        'newCasesByPublishDate',
    ]

    prettyprint.pprint(rt_on_fields)

    for c in rt_on_fields + ['{}_smoothed'.format(c) for c in rt_on_fields]:
        df['{}_Rt'.format(c)] = naive.compute_Rt(df[c], alpha=alpha, beta=beta).fillna(0)

def RSVD_smooth_data(df, alpha, beta, season_period=7, trend_alpha=100., difference_degree=2):

    initial_cols = df.columns

    filter_columns = [
        'newCasesByPublishDate',
    ]

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