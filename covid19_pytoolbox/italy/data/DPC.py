import os
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

    df['nuovi_casi_da_sospetto_diagnostico'] = (
        df.casi_da_sospetto_diagnostico -
        df.casi_da_sospetto_diagnostico.shift(1)
    ).fillna(0)

    df['nuovi_casi_da_screening'] = (
        df.casi_da_screening -
        df.casi_da_screening.shift(1)
    ).fillna(0)


    df['tamponi_giornalieri'] = (df.tamponi - df.tamponi.shift(1)).fillna(0)
    df['dimessi_guariti_giornalieri'] = (df.dimessi_guariti - df.dimessi_guariti.shift(1)).fillna(0)
    df['deceduti_giornalieri'] = (df.deceduti - df.deceduti.shift(1)).fillna(0)


    return TIMESTEPS, FIRST_CASI_SOSP_DIAGNOSTICO
