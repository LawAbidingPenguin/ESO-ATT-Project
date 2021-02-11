import pandas as pd
from datetime import datetime
import pytz
import get_data
import numpy as np
import time

def weeks_2021():
    weeks = pd.interval_range(start=pd.Timestamp('2021-01-01T14', tz='utc'), periods=52, freq='W-TUE')

    return weeks

if __name__ == '__main__':
    week_intervals = weeks_2021()

    att_df = get_data.att_data()
    att_df['date'] = att_df['timestamp'].apply(lambda x: datetime.utcfromtimestamp(x))
    att_df['interval'] = pd.cut(att_df['date'], bins=week_intervals)
    att_df['week'] = att_df['interval'].apply(lambda x: list(week_intervals).index(x)+1)
    att_df.drop('interval', axis=1, inplace=True)