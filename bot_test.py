import os
import re
import discord
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
            new_num.insert(i, ',')
    else:
        for i in range(len(num)%3, len(num)+int(len(num)/3), 4):
            new_num.insert(i, ',')

    return ''.join(new_num)


# Setting up the bot
intents = discord.Intents.default()
intents.members = True
bot = Bot(command_prefix='!', intents=intents)

@bot.command()
async def thisweek(ctx):
    msg = ctx.message.content

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
    
    bot_img = bot.user.avatar_url

    embed = discord.Embed(title=f"{seller} current trade week sales", colour=0xFFD700)
    for g in guilds:
        embed.add_field(name=f'{g}', value=f"{add_spaces(guild_sales[g])}", inline=False)
    embed.add_field(name='All Sales', value=f"{add_spaces(sales)}", inline=False)
    embed.set_footer(text=f"Last updated(UTC): {file_mod_time}")
    embed.set_thumbnail(url=bot_img)

    await ctx.send(embed=embed)

@bot.command()
async def lastweek(ctx):
    msg = ctx.message.content 

    wi = get_week()

    interval = [ weeks[wi-1][0], weeks[wi-1][1]]
    seller_input = msg.split()[1]
    data = get_sales(seller_input, interval)

    seller = data[0]
    sales = data[1]
    guild_sales = data[2]

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")

    bot_img = bot.user.avatar_url

    embed = discord.Embed(title=f"{seller} previous trade week sales", colour=0xFFD700)
    for g in guilds:
        embed.add_field(name=f'{g}', value=f"{add_spaces(guild_sales[g])}", inline=False)
    embed.add_field(name='All Sales', value=f"{add_spaces(sales)}", inline=False)
    embed.set_footer(text=f"Last updated(UTC): {file_mod_time}")
    embed.set_thumbnail(url=bot_img)

    await ctx.send(embed=embed)

# get sales for n previous days
@bot.command()
async def days(ctx):
    msg = ctx.message.content.replace('!days ', '') 

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

    bot_img = bot.user.avatar_url

    embed = discord.Embed(title=f"{seller} last {d} days sales", colour=0xFFD700)
    for g in guilds:
        embed.add_field(name=f'{g}', value=f"{add_spaces(guild_sales[g])}", inline=False)
    embed.add_field(name='All Sales', value=f"{add_spaces(sales)}", inline=False)
    embed.set_footer(text=f"Last updated(UTC): {file_mod_time}")
    embed.set_thumbnail(url=bot_img)

    await ctx.send(embed=embed)

# get most sold item
@bot.command()
async def mostsold(ctx):

    wi = get_week()
    interval = [ weeks[wi][0], weeks[wi][1]]

    cw_df = df[df['timestamp'].between(interval[0], interval[1])]

    most_sold = cw_df['item_link'].value_counts()
    ms_link = most_sold.idxmax()
    ms_sales = most_sold.iloc[0]
    avg_price_cw = int(cw_df[cw_df['item_link']==ms_link]['price'].mean())
    avg_price_30 = int(df[df['item_link']==ms_link]['price'].mean())

    item_id = re.search('(?<=\:)\d+', ms_link).group()

    session = req.HTMLSession()
    r = session.get(f'https://esoitem.uesp.net/itemSearch.php?version=&text={item_id}')
    links = r.html.absolute_links

    img_check = f'itemid={item_id}&summary&none=item.png'
    links = [l for l in links if img_check in l]
    # most sold image
    ms_img = links[0]

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")

    embed = discord.Embed(title='Most sold', description='Most sold item during current trade week', 
                                             colour=0xFFD700)
    embed.add_field(name='Trades made', value=f'{ms_sales}', inline=False)
    embed.add_field(name='Average price this trade week', value=f'{add_spaces(avg_price_cw)}', inline=False)
    embed.add_field(name='Average price last 30 days', value=f'{add_spaces(avg_price_30)}', inline=False)
    embed.set_footer(text=f"Last updated(UTC): {file_mod_time}")
    embed.set_image(url=ms_img)

    await ctx.send(embed=embed)

# get most valuable item
@bot.command()
async def mostvaluable(ctx):

    wi = get_week()
    interval = [ weeks[wi][0], weeks[wi][1]]
    cw_df = df[df['timestamp'].between(interval[0], interval[1])]

    mv_row = cw_df.loc[cw_df['price'].idxmax()]
    item_id = re.search('(?<=\:)\d+', mv_row['item_link']).group()

    session = req.HTMLSession()
    r = session.get(f'https://esoitem.uesp.net/itemSearch.php?version=&text={item_id}')
    links = r.html.absolute_links
    img_check = f'itemid={item_id}&summary&none=item.png'
    links = [l for l in links if img_check in l]
    mv_img = links[0]

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")

    embed = discord.Embed(title='Most valuable', description='Highest trade made during current trade week', 
                                             colour=0xFFD700)
    embed.add_field(name='Seller', value=f"{mv_row['seller_name']}", inline=False)
    embed.add_field(name='Price', value=f"{add_spaces(mv_row['price'])}", inline=False)
    embed.set_footer(text=f"Last updated(UTC): {file_mod_time}")
    embed.set_image(url=mv_img)

    await ctx.send(embed=embed)

@bot.command()
async def top5(ctx):
    msg = ctx.message.content
    nl = '\n' # newline to be used in f-string
    ws = '\u200b' # whitespace
    wi = get_week() # week index
    i = [ weeks[wi][0], weeks[wi][1]] # interval


    if msg.split()[1] == 'traders':
        embed = discord.Embed(title='Top5 highest sellers this trade week', colour=0xFFD700)
        
        for g in guilds:
            t5 = df[(df['guild_name']==g) & 
                    (df['timestamp'].between(i[0], i[1]))
                    ].groupby('seller_name')['price'].sum()
            t5.sort_values(ascending=False, inplace=True)

            t5_pairs = [f"{t5.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(t5.iloc[n])}" for n in range(5)]
            embed.add_field(name=f'{g}', value=f"{nl.join(t5_pairs)}", inline=False)

        # all guild sales
        ags = df[df['timestamp'].between(i[0], i[1])].groupby('seller_name')['price'].sum()
        ags.sort_values(ascending=False, inplace=True)

        ags_pairs = [f'{ags.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(ags.iloc[n])}' for n in range(5)]

        embed.add_field(name='All Guilds', value=f"{nl.join(ags_pairs)}",
                                                 inline=False)
    elif msg.split()[1] == 'buyers':
        embed = discord.Embed(title='Top5 biggest internal purchasers this trade week', colour=0xFFD700)

        for g in guilds:
            t5 = df[(df['guild_name']==g) & 
                    (df['timestamp'].between(i[0], i[1])) &
                    (df['internal']==1)
                    ].groupby('buyer_name')['price'].sum()
            t5.sort_values(ascending=False, inplace=True)

            t5_pairs = [f"{t5.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(t5.iloc[n])}" for n in range(5)]
            embed.add_field(name=f'{g}', value=f"{nl.join(t5_pairs)}", inline=False)

        # all guild buys
        agb = df[(df['timestamp'].between(i[0], i[1])) &
                 (df['internal']==1)].groupby('buyer_name')['price'].sum()
        agb.sort_values(ascending=False, inplace=True)

        agb_pairs = [f'{agb.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(agb.iloc[n])}' for n in range(5)]
        embed.add_field(name='All Guilds', value=f"{nl.join(agb_pairs)}", inline=False)
    else:
        embed = discord.Embed(title=f'No option **{msg.split()[1]}**, please choose **traders** or **buyers**')

    await ctx.send(embed=embed)

@bot.command()
async def summary(ctx):
    #TODO add total sales for each guild

    nl = '\n' # newline to be used in f-string
    wi = get_week()
    i = [ weeks[wi-1][0], weeks[wi-1][1]] # interval
    ws = '\u200b' # whitespace
    cw = datetime.now(timezone.utc).isocalendar()[1] # current week to be displayed in the title

    embed = discord.Embed(title=f"Trading summary: Week {cw}", colour=0xFFD700)
    
    for g in guilds:
        # ts - top sellers
        ts = df[(df['guild_name']==g) & 
                (df['timestamp'].between(i[0], i[1]))
                ].groupby('seller_name')['price'].sum()
        ts.sort_values(ascending=False, inplace=True)
        # tb - top buyers
        tb = df[(df['guild_name']==g) & 
                    (df['timestamp'].between(i[0], i[1])) &
                    (df['internal']==1)
                    ].groupby('buyer_name')['price'].sum()
        tb.sort_values(ascending=False, inplace=True)

        tb_pairs = [f"{tb.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(tb.iloc[n])}" for n in range(10)]
        ts_pairs = [f"{ts.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(ts.iloc[n])}" for n in range(10)]


        embed.add_field(name=f'{g}\n', value=f"Sales;\n\n"
                                             f"{nl.join(ts_pairs)}\n{ws}")
        embed.add_field(name=f'{ws}\n', value=f"Internal purchases;\n\n"
                                              f"{nl.join(tb_pairs)}\n{ws}")
        embed.add_field(name=f'{ws}', value=f'{ws}')

    # all guild sales
    ags = df[df['timestamp'].between(i[0], i[1])].groupby('seller_name')['price'].sum()
    ags.sort_values(ascending=False, inplace=True)

    ags_pairs = [f'{ags.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(ags.iloc[n])}' for n in range(10)]

    embed.add_field(name='All Guilds\n', value="Sales;\n\n"
                                               f"{nl.join(ags_pairs)}\n{ws}")

    # all guild buys
    agb = df[(df['timestamp'].between(i[0], i[1])) &
             (df['internal']==1)].groupby('buyer_name')['price'].sum()
    agb.sort_values(ascending=False, inplace=True)

    agb_pairs = [f'{agb.index[n]}: {ws} {ws} {ws} {ws} {add_spaces(agb.iloc[n])}' for n in range(10)]

    embed.add_field(name=f'{ws}\n', value="Internal purchases;\n\n"
                                          f"{nl.join(agb_pairs)}")
    embed.add_field(name=f'{ws}', value=f'{ws}')

    total_sales = df[df['timestamp'].between(i[0], i[1])]['price'].sum()
    total_buys = df[(df['timestamp'].between(i[0], i[1])) &
                 (df['internal']==1)]['price'].sum()
    embed.add_field(name='Total', value="Sales;\n\n"
                                        f"{add_spaces(total_sales)}\n\n")
    embed.add_field(name=f'{ws}\n', value='Purchases;\n\n'
                                          f'{add_spaces(total_buys)}\n\n')

    file_mod_time = datetime.fromtimestamp(os.path.getmtime('att_data.csv'), 
                    timezone.utc).strftime("%H:%M:%S %d-%m-%Y ")
    embed.set_footer(text=f"Last updated(UTC): {file_mod_time}")

    await ctx.send(embed=embed)

# most frequent buyers
@bot.command()
async def admirer(ctx):

    msg = ctx.message.content
    
    msg_input = msg.split()[1]
    seller = fix_seller_name(msg_input)[1]

    buyer_row = df[df['seller_name'].str.lower()==seller.lower()]['buyer_name'].value_counts()
    buyer_name = buyer_row.idxmax()
    purchases = buyer_row.iloc[0]

    await ctx.send(f"`Most frequent buyer(30 days) is {buyer_name} with {purchases} purchases.`")

@bot.command()
async def guildadmirer(ctx):

    msg = ctx.message.content
    
    msg_input = msg.split()[1]
    seller = fix_seller_name(msg_input)[1]

    buyer_row = df[(df['seller_name'].str.lower()==seller.lower()) & (df['internal']==1)]['buyer_name'].value_counts()
    buyer_name = buyer_row.idxmax()
    purchases = buyer_row.iloc[0]

    await ctx.send(f"`Most frequent guildie buyer(30 days) is {buyer_name} with {purchases} purchases.`")

@bot.command()
async def roast(ctx):
    pass
    #TODO create a roast command

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, discord.ext.commands.CommandInvokeError):
        print(error)
        await ctx.send(f'`No info found...`')
    #TODO add code to write to an error logging file


if __name__ == '__main__':

    load_dotenv('.env')
    bot.run(os.getenv('DISCORD_TOKEN'))
    #TODO testing git