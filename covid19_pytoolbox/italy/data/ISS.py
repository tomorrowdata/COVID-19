import datetime
import os
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
import pprint
prettyprint = pprint.PrettyPrinter(indent=4)

from covid19_pytoolbox.utils import RSVD_smooth_data_generic
from covid19_pytoolbox import settings

def read_weekly_Rt_from_local(path='sources/Rt_from_ISS.csv'):

    ISS_Rt = pd.read_csv(
        os.path.join(settings.BASE_DATA_PATH, path),
        parse_dates=['computation_time_range_start', 'computation_time_range_end']
    )
    return ISS_Rt


def preprocess(df):
    ISS_Rt_clean = df.loc[:,[
        'computation_time_range_start','computation_time_range_end','Rt','Rt_95_min','Rt_95_max'
    ]].dropna()

    ISS_Rt_clean['Rt_95_err_max'] = ISS_Rt_clean.Rt_95_max - ISS_Rt_clean.Rt
    ISS_Rt_clean['Rt_95_err_min'] = ISS_Rt_clean.Rt - ISS_Rt_clean.Rt_95_min
    
    ISS_Rt_clean['Rt_reference_date'] = (
        (
            ISS_Rt_clean.computation_time_range_start + 
            (ISS_Rt_clean.computation_time_range_end - ISS_Rt_clean.computation_time_range_start)/2
        ).dt.normalize()+timedelta(days=1, minutes=-1)
    )

    ISS_Rt_clean.sort_values(by='Rt_reference_date', inplace=True)
    ISS_Rt_clean.reset_index(inplace=True, drop=True)    

    return ISS_Rt_clean

def export_Rt_clean(df, path='computed/Rt_from_ISS_processed.{}'):
    ISS_Rt_clean_save = df[[
        'computation_time_range_start', 'computation_time_range_end', 'Rt_reference_date', 
        'Rt', 'Rt_95_min', 'Rt_95_max'
    ]]

    ISS_Rt_clean_save.to_csv(
        os.path.join(settings.BASE_DATA_PATH, path.format('csv')),
        float_format='%.2f',
        index=False        
    )
    ISS_Rt_clean_save.to_excel(
        os.path.join(settings.BASE_DATA_PATH, path.format('xlsx')),
        float_format='%.2f',
        index=False        
    )

def read_weekly_cases_from_local(limit_date=None, path='sources/ISS_weekly_local_imported_cases/'):
    if not limit_date:
        limit_date=datetime.now()

    # scan path to find the latest file before limit_date
    _path = os.path.join(settings.BASE_DATA_PATH, path)

    max_available_date = max(
        filter(
            lambda date: date<=limit_date,
            map(
                lambda filename: datetime.strptime(filename.replace('curva_epidemica_Italia_',''), '%Y-%m-%d'),
                os.listdir(os.path.join(settings.BASE_DATA_PATH,'sources/ISS_weekly_local_imported_cases/'))
            )
        )
    )

    filename = f'curva_epidemica_Italia_{max_available_date:%Y-%m-%d}'
    print(filename)

    return pd.read_csv(
        os.path.join(_path, filename),
        names=["data", "local", "imported"],
        parse_dates=["data"],
        sep=" "
    )

def preprocess_cases(df):

    df["total"] = df.local+df.imported
    df["imported_ratio"] = df.imported/df.total
    df['imported_ratio_avg14'] = df.imported_ratio.rolling(window=14, min_periods=1).mean()
    df['imported_ratio_std14'] = df.imported_ratio.rolling(window=14, min_periods=1).std()

def RSVD_smooth_data(df, alpha, beta, season_period=7, trend_alpha=100., difference_degree=2):

    filter_columns = [
        'total',
        'imported',
    ]

    RSVD_smooth_data_generic(df, filter_columns, alpha, beta, season_period, trend_alpha, difference_degree)
