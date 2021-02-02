import re
import pandas as pd
import io
import time

# start = time.perf_counter()

df_list = []
for i in range(1, 17):
    att = f'ArkadiusTradeToolsSalesData{i:02d}.lua'

    with open(att, 'rb') as file:
        dirty_data = file.readlines()

    dirty_data = [str(x) for x in dirty_data]
    data = [x for x in dirty_data if '[\"unitPrice\"]' not in x]
    data = data[6:-4]
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
    df_list.append(df)

att_df = pd.concat(df_list)
# end = time.perf_counter()
# print(end-start)