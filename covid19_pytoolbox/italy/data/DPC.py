import os
import pprint
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from covid19_pytoolbox.modeling.Rt import naive
from covid19_pytoolbox.smoothing.seasonalRSVD.LogRSVD import LogSeasonalRegularizer
from covid19_pytoolbox.utils import smape, padnan


prettyprint = pprint.PrettyPrinter(indent=4)


def load_daily_cases_from_github():
    def parse_date(date):
        return datetime.strptime(date[:10], '%Y-%m-%d')

    df = pd.read_csv(
        'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv',
        parse_dates=['data'],
        date_parser=parse_date
    )
    return df

def load_daily_cases_from_github_region(region):
    def parse_date(date):
        return datetime.strptime(date[:10] + " 23:59:00", "%Y-%m-%d %H:%M:%S")

    regions_raw_data = pd.read_csv(
        'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv',
        parse_dates=['data'],
        date_parser=parse_date
    )
    regional_raw_data = regions_raw_data.loc[regions_raw_data.denominazione_regione==region].reset_index().copy()
    return regional_raw_data

def preprocess(df):

    TIMESTEPS = len(df.nuovi_positivi)

    FIRST_CASI_SOSP_DIAGNOSTICO = df.casi_da_sospetto_diagnostico.first_valid_index()

    df.casi_da_sospetto_diagnostico.fillna(0, inplace=True)
    df.casi_da_screening.fillna(0, inplace=True)

    return TIMESTEPS, FIRST_CASI_SOSP_DIAGNOSTICO

def compute_first_diffs(df):

    def first_diff(df, col):
        return (df[col] - df[col].shift(1)).fillna(0)

    cols = {
        'nuovi_casi_da_sospetto_diagnostico': 'casi_da_sospetto_diagnostico',
        'nuovi_casi_da_screening': 'casi_da_screening',
        'tamponi_giornalieri': 'tamponi',
        'dimessi_guariti_giornalieri': 'dimessi_guariti',
        'deceduti_giornalieri': 'deceduti'
    }

    prettyprint.pprint(cols)


    for diffcol, col in cols.items():
        df[diffcol] = first_diff(df, col)


def tikhonov_smooth_differentiate(df, regularizer):

    cols = {
        'tamponi_giornalieri_smoothed': 'tamponi',
        'dimessi_guariti_giornalieri_smoothed': 'dimessi_guariti',
        'deceduti_giornalieri_smoothed': 'deceduti',
        'nuovi_positivi_smoothed': 'totale_casi',
        'nuovi_casi_da_sospetto_diagnostico_smoothed': 'casi_da_sospetto_diagnostico',
        'nuovi_casi_da_screening_smoothed': 'casi_da_screening'
    }

    prettyprint.pprint(cols)

    for smoothcol, col in cols.items():
        print(smoothcol, end=' - ')
        df[smoothcol] = regularizer.stat_smooth_differentiate(df[col])

def tikhonov_smooth_data(df, regularizer):

    filter_columns = [
        'ricoverati_con_sintomi', 'terapia_intensiva',
        'isolamento_domiciliare', 'totale_positivi',
        'dimessi_guariti', 'deceduti', 'tamponi', 'totale_casi', 'casi_da_screening',
        'casi_da_sospetto_diagnostico'
    ]

    prettyprint.pprint(filter_columns)

    for col in filter_columns:
        smoothcol = col+'_smoothed'
        print(smoothcol, end=' - ')
        df[smoothcol] = regularizer.stat_smooth_data(df[col])

def compute_residuals(df):

    df['nuovi_positivi_residuals'] = (
        df.nuovi_positivi - df.nuovi_positivi_smoothed
    )
    df['nuovi_positivi_relative_residuals'] = (
        df.nuovi_positivi_residuals / df.nuovi_positivi_smoothed
    )
    df.loc[0,'nuovi_positivi_relative_residuals'] = 0

def bulk_compute_naive_Rt(df, alpha, beta):

    rt_on_fields = [
        'nuovi_positivi',
        'nuovi_casi_da_sospetto_diagnostico',
        'nuovi_casi_da_screening'
    ]

    prettyprint.pprint(rt_on_fields)

    for c in rt_on_fields + ['{}_smoothed'.format(c) for c in rt_on_fields]:
        df['{}_Rt'.format(c)] = naive.compute_Rt(df[c], alpha=alpha, beta=beta).fillna(0)

def RSVD_smooth_data(df, alpha, beta, season_period=7, trend_alpha=100., difference_degree=2):

    initial_cols = df.columns

    filter_columns = [
        'nuovi_positivi',
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