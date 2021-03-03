import os
import time
import pandas as pd
from datetime import datetime
import get_data

def trade_weeks():
    weeks = pd.interval_range(start=pd.Timestamp('2021-01-01T14', tz='utc'), periods=208, freq='W-TUE')
    return weeks

if __name__ == '__main__':

    week_intervals = trade_weeks()
    # starting time when file was modified
    start_time = os.path.getmtime('ArkadiusTradeToolsSalesData01.lua')

    weeks = []
    for n in range(0, len(week_intervals)):
        x = n / 52

        if x >= 1:
            weeks.append(f"{str(week_intervals[n].left)[:4]}_week{n-(int(x)*52)+1}")   
        else:
            weeks.append(f"{str(week_intervals[n].left)[:4]}_week{n+1}")

    att_df = get_data.att_data()
    att_df['date'] = att_df['timestamp'].apply(lambda x: datetime.utcfromtimestamp(x))
    att_df['interval'] = pd.cut(att_df['date'], bins=week_intervals)
    # att_df['week'] = att_df['interval'].apply(lambda x: list(week_intervals).index(x)+1)
    # att_df.drop('interval', axis=1, inplace=True)
    att_df = att_df[att_df['guild_name'].isin(['Rolling Coins', 'Shining Coins', 'Flipping Coins'])]
    [print(weeks[list(week_intervals).index(x)]) for x in att_df.head()['interval'].values]

    # print(att_df.head())


    # while True:
    #     time.sleep(1)
    #     # new time when file was last modified
    #     new_time = os.path.getmtime('ArkadiusTradeToolsSalesData01.lua')

    #     if start_time != new_time:
            
    #         att_df = get_data.att_data()
    #         att_df['date'] = att_df['timestamp'].apply(lambda x: datetime.utcfromtimestamp(x))
    #         att_df['interval'] = pd.cut(att_df['date'], bins=week_intervals)
    #         # att_df['week'] = att_df['interval'].apply(lambda x: list(week_intervals).index(x)+1)
    #         # att_df.drop('interval', axis=1, inplace=True)
    #         att_df = att_df[att_df['guild_name'].isin(['Rolling Coins', 'Shining Coins', 'Flipping Coins'])]

    #         start_time = new_time

    