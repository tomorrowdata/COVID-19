import os
import pprint
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from covid19_pytoolbox.modeling import Rt

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
        df['{}_Rt'.format(c)] = Rt.compute_naive_Rt(df[c], alpha=alpha, beta=beta).fillna(0)