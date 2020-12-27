import os
import pandas as pd
import numpy as np
from datetime import timedelta

from covid19_pytoolbox.settings import BASE_DATA_PATH

def read_weekly_Rt_from_local(path='sources/Rt_from_ISS.csv'):

    ISS_Rt = pd.read_csv(
        os.path.join(BASE_DATA_PATH, path),
        parse_dates=['computation_time_range_start', 'computation_time_range_end']
    )
    return ISS_Rt


def clean_weekly_Rt(df):
    ISS_Rt_clean = df.loc[:,[
        'computation_time_range_start','computation_time_range_end','Rt','Rt_95_min','Rt_95_max'
    ]].dropna()

    ISS_Rt_clean['Rt_95_err_max'] = ISS_Rt_clean.Rt_95_max - ISS_Rt_clean.Rt
    ISS_Rt_clean['Rt_95_err_min'] = np.abs(ISS_Rt_clean.Rt_95_max - ISS_Rt_clean.Rt)

    ISS_Rt_clean['Rt_reference_date'] = (
        (
            ISS_Rt_clean.computation_time_range_start + 
            (ISS_Rt_clean.computation_time_range_end - ISS_Rt_clean.computation_time_range_start)/2
        ).dt.normalize()+timedelta(days=1, minutes=-1)
    )

    return ISS_Rt_clean

def export_Rt_clean(df, path='computed/Rt_from_ISS_processed.{}'):
    ISS_Rt_clean_save = df[[
        'computation_time_range_start', 'computation_time_range_end', 'Rt_reference_date', 
        'Rt', 'Rt_95_min', 'Rt_95_max'
    ]]

    ISS_Rt_clean_save.to_csv(
        os.path.join(BASE_DATA_PATH, path.format('csv')),
        float_format='%.2f',
        index=False        
    )
    ISS_Rt_clean_save.to_excel(
        os.path.join(BASE_DATA_PATH, path.format('xlsx')),
        float_format='%.2f',
        index=False        
    )