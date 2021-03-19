import discord
import pandas as pd
from datetime import datetime, timezone

week_intervals = pd.interval_range(start=pd.Timestamp('2021-01-01T14', tz='utc'), periods=208, freq='W-TUE')
# turning week_intervals to timestamp intervals
weeks = []
for i in week_intervals.to_tuples():
    weeks.append((int(i[0].to_pydatetime().timestamp()), int(i[1].to_pydatetime().timestamp())))

# Getting current trade week
utc_time = datetime.now(timezone.utc)
def get_week(interval):
    start = datetime.fromtimestamp(interval[0], timezone.utc)
    end = datetime.fromtimestamp(interval[1], timezone.utc)

    if start <= utc_time <= end:
        return True
    else:
        return False

for interval in weeks:
    if get_week(interval):
        # Week index
        wi = weeks.index(interval)

df = pd.read_csv('test_file.csv', index_col=9)

def current_sales(seller, interval=[weeks[wi][0], weeks[wi][1]]):
    sales = df[(df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1]))]['price'].sum()
    return sales

def previous_sales(seller, interval=[weeks[wi-1][0], weeks[wi-1][1]]):
    sales = df[(df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1]))]['price'].sum()
    return sales

# adding spaces to sales 
def add_spaces(num):
    num = str(num)
    new_num = list(num)
    if len(num) % 3 == 0:
        for i in range(3, len(num)+int(len(num)/3)-1, 4):
            new_num.insert(i, ' ')
    else:
        for i in range(len(num)%3, len(num)+int(len(num)/3), 4):
            new_num.insert(i, ' ')
        

    return ''.join(new_num)

class MyClient(discord.Client):

    async def on_ready(self):
        print(f"We have logged in as {self.user}!")

    async def on_message(self, message):
        msg = message.content
        chl = message.channel

        if msg.startswith('!sales'):
            seller = msg.split()[1]
            await chl.send(f"`{seller}: {add_spaces(current_sales(seller))}`")
        elif msg.startswith('!last'):
            seller = msg.split()[1]
            await chl.send(f"`{seller}: {add_spaces(previous_sales(seller))}`")

if __name__ == '__main__':

    client = MyClient()
    client.run('')
