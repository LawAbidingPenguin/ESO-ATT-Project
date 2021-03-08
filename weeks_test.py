import pandas as pd
from csv_data import get_csv
import io
from datetime import datetime, timezone

def trade_weeks():
    weeks = pd.interval_range(start=pd.Timestamp('2021-01-01T14', tz='utc'), periods=208, freq='W-TUE')
    return weeks

if __name__ == '__main__':

    week_intervals = trade_weeks()

    weeks = []
    for i in week_intervals.to_tuples():
        weeks.append((int(i[0].to_pydatetime().timestamp()), int(i[1].to_pydatetime().timestamp())))

    current = datetime.now(timezone.utc)
    def get_week(interval):
        start = datetime.fromtimestamp(interval[0], timezone.utc)
        end = datetime.fromtimestamp(interval[1], timezone.utc)
        if start <= current <= end:
            return True
        else:
            return False

    for interval in weeks:
        if get_week(interval):
            # Week index
            wi = weeks.index(interval)

    df = pd.read_csv(io.StringIO(get_csv()))
    print(df[ (df['seller_name'] == 'Fiktius') & (df['timestamp'].between(weeks[wi][0], weeks[wi][1]) )]['price'].sum())