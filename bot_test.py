import os
from discord import guild
import pandas as pd
from dotenv import load_dotenv
from discord.ext.commands import Bot
from datetime import datetime, timezone


guilds = ['Rolling Coins', 'Shining Coins', 'Flipping Coins']

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

    guild_sales = {}
    for g in guilds:

        guild_sales[g] = df[ (df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1])) & 
                             (df['guild_name'] == g)]['price'].sum()

    name = df[df['seller_name'].str.lower() == seller.lower()]['seller_name'].unique()[0]
    sales = df[(df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1]))]['price'].sum()

    if '\\' in name:
        name = name.replace('\\', '')

    return (name, sales, guild_sales)

# getting previous trade week sales
def previous_sales(seller, interval=[weeks[wi-1][0], weeks[wi-1][1]]):

    if '\'' in seller:
        seller = '\\\''.join(seller.split('\''))

    guild_sales = {}
    for g in guilds:

        guild_sales[g] = df[ (df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1])) & 
                             (df['guild_name'] == g)]['price'].sum()

    name = df[df['seller_name'].str.lower() == seller.lower()]['seller_name'].unique()[0]
    sales = df[(df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1]))]['price'].sum()

    if '\\' in name:
        name = name.replace('\\', '')

    return (name, sales, guild_sales)

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

# Setting up the bot
bot = Bot(command_prefix='!')

@bot.command()
async def thisweek(cxt):
    msg = cxt.message.content
    chl = cxt.channel

    msg_input = msg.split()[1]
    data = current_sales(msg_input)
    seller = data[0]
    sales = data[1]
    guild_sales = data[2]       

    await chl.send(f"**{seller}** current trade week sales:\n"
                   f"```\n"
                   f"Rolling Coins: {add_spaces(guild_sales['Rolling Coins'])}\n"
                   f"Shining Coins: {add_spaces(guild_sales['Shining Coins'])}\n"
                   f"Flipping Coins: {add_spaces(guild_sales['Flipping Coins'])}\n"
                   f"All Sales: {add_spaces(sales)}\n"
                    "```")

@bot.command()
async def lastweek(cxt):
    msg = cxt.message.content
    chl = cxt.channel 

    msg_input = msg.split()[1]
    data = previous_sales(msg_input)
    seller = data[0]
    sales = data[1]
    guild_sales = data[2]       

    await chl.send(f"**{seller}** last trade week sales:\n"
                   f"```\n"
                   f"Rolling Coins: {add_spaces(guild_sales['Rolling Coins'])}\n"
                   f"Shining Coins: {add_spaces(guild_sales['Shining Coins'])}\n"
                   f"Flipping Coins: {add_spaces(guild_sales['Flipping Coins'])}\n"
                   f"All Sales: {add_spaces(sales)}\n"
                    "```")

if __name__ == '__main__':

    load_dotenv('.env')
    bot.run(os.getenv('DISCORD_TOKEN'))
