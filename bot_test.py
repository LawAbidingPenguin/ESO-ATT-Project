import os
import re
import pandas as pd
import requests_html as req
from dotenv import load_dotenv
from discord.ext.commands import Bot
from datetime import datetime, timezone, timedelta

guilds = ['Rolling Coins', 'Shining Coins', 'Flipping Coins']
df = pd.read_csv('att_data.csv', index_col=9)

# creating custom trade week intervals
week_intervals = pd.interval_range(start=pd.Timestamp('2021-01-01T14', tz='utc'), periods=208, freq='W-TUE')
# turning week_intervals to timestamp intervals (to be used with get_week()) 
weeks = []
for i in week_intervals.to_tuples():
    weeks.append((int(i[0].to_pydatetime().timestamp()), int(i[1].to_pydatetime().timestamp())))

# fixing names
# to be used inside df
def fix_seller_name(seller):

    if '\'' in seller:
        seller = '\\\''.join(seller.split('\''))
        name = df[df['seller_name'].str.lower() == seller.lower()]['seller_name'].unique()[0]
    elif r'\xc3' in str(seller.encode('utf-8')):
        name = seller
        seller = str(seller.encode('utf-8'))[2:-1]
    else:
        name = df[df['seller_name'].str.lower() == seller.lower()]['seller_name'].unique()[0]

    return (name, seller)

# Getting current trade week
def get_week():
    utc_time = datetime.now(timezone.utc)

    for interval in weeks:
        start = datetime.fromtimestamp(interval[0], timezone.utc)
        end = datetime.fromtimestamp(interval[1], timezone.utc)

        if start <= utc_time <= end:
            return weeks.index(interval)

def get_sales(seller, interval):

    name, seller = fix_seller_name(seller)

    guild_sales = {}
    for g in guilds:

        guild_sales[g] = df[ (df['seller_name'].str.lower() == seller.lower()) & (df['timestamp'].between(interval[0],interval[1])) & 
                             (df['guild_name'] == g)]['price'].sum()

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

    # week index
    wi = get_week()

    interval = [ weeks[wi][0], weeks[wi][1]]
    seller_input = msg.split()[1]
    data = get_sales(seller_input, interval)

    seller = data[0]
    sales = data[1]
    guild_sales = data[2]       

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")

    await chl.send(f"**{seller}** current trade week sales:\n"
                   f"```\n"
                   f"Rolling Coins: {add_spaces(guild_sales['Rolling Coins'])}\n"
                   f"Shining Coins: {add_spaces(guild_sales['Shining Coins'])}\n"
                   f"Flipping Coins: {add_spaces(guild_sales['Flipping Coins'])}\n"
                   f"All Sales: {add_spaces(sales)}\n\n"
                   f"Last updated(UTC): {file_mod_time}\n"
                    "```")

@bot.command()
async def lastweek(cxt):
    msg = cxt.message.content
    chl = cxt.channel 

    wi = get_week()

    interval = [ weeks[wi-1][0], weeks[wi-1][1]]
    seller_input = msg.split()[1]
    data = get_sales(seller_input, interval)

    seller = data[0]
    sales = data[1]
    guild_sales = data[2]

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")

    await chl.send(f"**{seller}** last trade week sales:\n"
                   f"```\n"
                   f"Rolling Coins: {add_spaces(guild_sales['Rolling Coins'])}\n"
                   f"Shining Coins: {add_spaces(guild_sales['Shining Coins'])}\n"
                   f"Flipping Coins: {add_spaces(guild_sales['Flipping Coins'])}\n"
                   f"All Sales: {add_spaces(sales)}\n\n"
                   f"Last updated(UTC): {file_mod_time}\n"
                    "```")

# get sales for n previous days
@bot.command()
async def days(cxt):
    msg = cxt.message.content.replace('!days ', '')
    chl = cxt.channel 

    # number of days
    d = int(msg.split()[0])
    utc_time = datetime.now(timezone.utc)
    seller_input = msg.split()[1]
    interval = [ (utc_time - timedelta(d)).timestamp(), utc_time.timestamp()]
    data = get_sales(seller_input, interval)

    seller = data[0]
    sales = data[1]
    guild_sales = data[2]

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")

    await chl.send(f"**{seller}** last {d} days sales:\n"
                   f"```\n"
                   f"Rolling Coins: {add_spaces(guild_sales['Rolling Coins'])}\n"
                   f"Shining Coins: {add_spaces(guild_sales['Shining Coins'])}\n"
                   f"Flipping Coins: {add_spaces(guild_sales['Flipping Coins'])}\n"
                   f"All Sales: {add_spaces(sales)}\n\n"
                   f"Last updated(UTC): {file_mod_time}\n"
                    "```")

# get most sold item
@bot.command()
async def mostsold(cxt):
    chl = cxt.channel

    most_sold = df['item_link'].value_counts().idxmax()
    item_id = re.search('(?<=\:)\d+', most_sold).group()

    session = req.HTMLSession()
    r = session.get(f'https://esoitem.uesp.net/itemSearch.php?version=&text={item_id}')
    links = r.html.absolute_links

    img_check = f'itemid={item_id}&summary&none=item.png'
    links = [l for l in links if img_check in l]
    # most sold image
    ms_img = links[0]

    await chl.send(ms_img)

# get most valuable item
@bot.command()
async def mostvaluable(cxt):
    chl = cxt.channel

    mv_row = df.loc[df['price'].idxmax()]
    
    item_id = re.search('(?<=\:)\d+', mv_row['item_link']).group()

    session = req.HTMLSession()
    r = session.get(f'https://esoitem.uesp.net/itemSearch.php?version=&text={item_id}')
    links = r.html.absolute_links
    img_check = f'itemid={item_id}&summary&none=item.png'
    links = [l for l in links if img_check in l]
    mv_img = links[0]

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")

    await chl.send(f"{mv_img}"
                   f"\n```Sold for {add_spaces(mv_row['price'])} by {mv_row['seller_name']}"
                   f"\nLast updated(UTC): {file_mod_time}```")

# most frequent buyers
@bot.command()
async def admirer(cxt):

    msg = cxt.message.content
    chl = cxt.channel
    
    msg_input = msg.split()[1]
    seller = fix_seller_name(msg_input)[1]

    buyer_row = df[df['seller_name'].str.lower()==seller.lower()]['buyer_name'].value_counts()
    buyer_name = buyer_row.idxmax()
    purchases = buyer_row.iloc[0]

    await chl.send(f"`Most frequent buyer(30 days) is {buyer_name} with {purchases} purchases.`")


@bot.command()
async def guildadmirer(cxt):

    msg = cxt.message.content
    chl = cxt.channel
    
    msg_input = msg.split()[1]
    seller = fix_seller_name(msg_input)[1]

    buyer_row = df[(df['seller_name'].str.lower()==seller.lower()) & (df['internal']==1)]['buyer_name'].value_counts()
    buyer_name = buyer_row.idxmax()
    purchases = buyer_row.iloc[0]

    await chl.send(f"`Most frequent guildie buyer(30 days) is {buyer_name} with {purchases} purchases.`")
    

if __name__ == '__main__':

    load_dotenv('.env')
    bot.run(os.getenv('DISCORD_TOKEN'))