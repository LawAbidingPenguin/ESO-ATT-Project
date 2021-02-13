import re
import pandas as pd
import io
from multiprocessing import Pool

att_list = [f'ArkadiusTradeToolsSalesData{i:02d}.lua' for i in range(1,17)]

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

    data = [','.join(row) for row in data]

    data = '\n'.join(data)
    columns = 'buyer_name,guild_name,internal,item_link,price,quantity,seller_name,taxes,timestamp,entry'
    csv_data = columns + '\n' + data

    # buyer_name, guild_name, internal, itemlink, price, quantity, seller_name, taxes, timestamp, index(entry)
    df = pd.read_csv(io.StringIO(csv_data), index_col=9)

    return df

def att_data():
    df_list = Pool().map(clean_data, att_list)
    att_df= pd.concat(df_list)

    return att_df

# if __name__ == '__main__':
#     att_data()
