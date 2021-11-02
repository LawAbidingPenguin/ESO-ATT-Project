#!/usr/bin/env python3.6
import re
import os
import time
import multiprocessing
from multiprocessing import Pool

guilds = ['Rolling Coins', 'Flipping Coins', 'Shining Coins']

att_list = [f'ArkadiusTradeToolsSalesData{i:02d}.lua' for i in range(1,17)]
columns = 'buyer_name,guild_name,internal,item_link,price,quantity,seller_name,taxes,timestamp,entry'

def clean_data(att):
    # Checking if file contains NA Megaserver data
    check = None
    with open(att, 'rb') as file:
        na_check = file.read()
        na_check = str(na_check)
        if 'NA Megaserver' in na_check:
            check = True
        else:
            check = False

    with open(att, 'rb') as file:
        dirty_data = file.readlines()

        if check == True:
            if "NA Megaserver" in na_check[:70]:
                dirty_data = dirty_data[12:-4]
            else:
                dirty_data = dirty_data[6:-10]

        elif check == False:
            dirty_data = dirty_data[6:-4]

    dirty_data = [str(x) for x in dirty_data]
    data = [x for x in dirty_data if '[\"unitPrice\"]' not in x]
    data = [data[i:i+11] for i in range(0, len(data), 12)]

    for row in data:
        row.pop(1)
        row.sort()
        for x in range(0, len(row)-1):            
            row[x] = row[x].split('=')[1].split(',')[0].strip()
            row[x] = row[x].strip('\"')

        row[9] = re.sub('\[|\]', '', re.search('\d+',row[9]).group())

    data = [x for x in data if x[1] in guilds]
    data = [','.join(row) for row in data]
    data = [x.replace('@', '') for x in data]
    data = '\n'.join(data)

    return data
    
def get_csv():
    csv_list = Pool(16).map(clean_data, att_list)
    csv = columns + '\n' + '\n'.join(csv_list)

    return csv


if __name__ == '__main__':
    multiprocessing.freeze_support()

    # with open('att_data.csv', 'w') as f:
    #     f.write(get_csv())

    if not os.path.isfile('att_data.csv'):
        with open('att_data.csv', 'w') as f:
            f.write(get_csv())        

    # start file modified time
    if not os.path.isfile('mod_time.txt'):
        with open('mod_time.txt', 'w') as f:
            f.write(f"{os.path.getmtime('ArkadiusTradeToolsSalesData16.lua')}")

    # Checking if modified time of att files has changed
    i = 1
    while True:

        new_mt = os.path.getmtime('ArkadiusTradeToolsSalesData16.lua')
        with open('mod_time.txt', 'r') as f:
            start_mt = float(f.read())

        if abs(new_mt - start_mt) > 5:

            time.sleep(5)

            with open('mod_time.txt', 'w') as f:
                f.write(f"{new_mt}")

            with open('att_data.csv', 'w') as f:
                f.write(get_csv())

            print(f'#{i} Updated csv...')
            i += 1