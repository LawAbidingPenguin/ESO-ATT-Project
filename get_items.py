from os import link
import pandas as pd
import requests_html as req
import re

if __name__ == '__main__':

    df = pd.read_csv('test_file.csv', index_col=9)
    item_id = re.search('(?<=\:)\d+', df.iloc[2]['item_link']).group()
    print(item_id)
    # item_id = 54173

    session = req.HTMLSession()
    r = session.get(f'https://esoitem.uesp.net/itemSearch.php?version=&text={item_id}')
    links = r.html.absolute_links
    img_check = f'itemid={item_id}&summary&none=item.png'
    links = [l for l in links if img_check in l]
    img = links[0]
    print(img)