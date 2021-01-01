import os
import pprint
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(cols)


    for diffcol, col in cols.items():
        df[diffcol] = first_diff(df, col)
