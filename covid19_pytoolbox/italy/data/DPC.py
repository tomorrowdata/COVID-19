import os
import pprint
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from covid19_pytoolbox.modeling.Rt import naive
from covid19_pytoolbox.smoothing.seasonalRSVD.LogRSVD import LogSeasonalRegularizer
from covid19_pytoolbox.utils import smape, padnan, RSVD_smooth_data_generic


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

    # compute hospitalized_cumulative cumulative value of hospitalized cases
    df['hospitalized_cumulative'] = df.totale_ospedalizzati + df.dimessi_guariti + df.deceduti

    return TIMESTEPS, FIRST_CASI_SOSP_DIAGNOSTICO

def compute_first_diffs(df):

    def first_diff(df, col):
        return (df[col] - df[col].shift(1)).fillna(0)

    cols = {
        'nuovi_casi_da_sospetto_diagnostico': 'casi_da_sospetto_diagnostico',
        'nuovi_casi_da_screening': 'casi_da_screening',
        'tamponi_giornalieri': 'tamponi',
        'dimessi_guariti_giornalieri': 'dimessi_guariti',
        'deceduti_giornalieri': 'deceduti',
        'nuovi_ospedalizzati': 'hospitalized_cumulative'
    }

    prettyprint.pprint(cols)


    for diffcol, col in cols.items():
        df[diffcol] = first_diff(df, col)

        # fix negative values for reporting errors, substituting them with the mean of the neighbours
        for idx in df.loc[df[diffcol]<0].index:
            df.loc[idx,[diffcol]] = (df.loc[idx+1,[diffcol]]+df.loc[idx-1,[diffcol]])/2.


def tikhonov_smooth_differentiate(df, regularizer):

    cols = {
        'tamponi_giornalieri_smoothed': 'tamponi',
        'dimessi_guariti_giornalieri_smoothed': 'dimessi_guariti',
        'deceduti_giornalieri_smoothed': 'deceduti',
        'nuovi_positivi_smoothed': 'totale_casi',
        'nuovi_casi_da_sospetto_diagnostico_smoothed': 'casi_da_sospetto_diagnostico',
        'nuovi_casi_da_screening_smoothed': 'casi_da_screening',
        'nuovi_ospedalizzati_smoothed': 'hospitalized_cumulative'
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

    filter_columns = [
        'nuovi_positivi',
        'tamponi_giornalieri',
        'nuovi_ospedalizzati'
    ]

    RSVD_smooth_data_generic(df, filter_columns, alpha, beta, season_period, trend_alpha, difference_degree)

def merge_ISS_weekly_cases(dpcdf, issdf):
    # fill last nan observations with the last available
    # they will be used as mean and std to sample possible imported ratios

    ###################################
    #TODO fix shift(8)
    ###################################

    df = pd.merge(left=dpcdf, right=issdf, how='left', on=['data'])
    df.set_index('data', inplace=True)
    df['imported_ratio_deseason_smoothed_shifted'] = \
        df.imported_ratio_deseason_smoothed.shift(8)
    df['imported_ratio_shifted'] = \
        df.imported_ratio.shift(8)

    df.reset_index(inplace=True)

    return df

def compute_cases_corrected_by_imported(df):
    df['nuovi_positivi_corrected_deseason_smoothed'] = \
        df.nuovi_positivi_deseason_smoothed*(1-df.imported_ratio_deseason_smoothed_shifted)
    df['nuovi_positivi_corrected'] = \
        (df.nuovi_positivi*(1-df.imported_ratio_shifted)).fillna(0.)
