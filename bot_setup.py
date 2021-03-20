import discord
import pandas as pd
from datetime import datetime, timezone

# creating custom trade week intervals
week_intervals = pd.interval_range(start=pd.Timestamp('2021-01-01T14', tz='utc'), periods=208, freq='W-TUE')
# turning week_intervals to timestamp intervals (to be used with get_week()) 
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
# getting current trade week sales
def current_sales(seller, interval=[weeks[wi][0], weeks[wi][1]]):

    if '\'' in seller:
        seller = '\\\''.join(seller.split('\''))

    name = df[df['seller_name'].str.lower() == seller.lower()]['seller_name'].unique()[0]
    sales = df[(df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1]))]['price'].sum()

    if '\\' in name:
        name = name.replace('\\', '')

    return (name, sales)

# getting previous trade week sales
def previous_sales(seller, interval=[weeks[wi-1][0], weeks[wi-1][1]]):

    if '\'' in seller:
        seller = '\\\''.join(seller.split('\''))

    name = df[df['seller_name'].str.lower() == seller.lower()]['seller_name'].unique()[0]
    sales = df[(df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1]))]['price'].sum()

    if '\\' in name:
        name = name.replace('\\', '')

    return (name, sales)

# adding spaces to sales number for readability
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
            data = current_sales(seller)

            await chl.send(f"`{data[0]}: {add_spaces(data[1])}`")
        elif msg.startswith('!lastweek'):
            seller = msg.split()[1]
            data = previous_sales(seller)

            await chl.send(f"`{data[0]}: {add_spaces(data[1])}`")

if __name__ == '__main__':

    client = MyClient()
    client.run('')
