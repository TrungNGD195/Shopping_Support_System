import pandas as pd
df_pos = pd.read_csv('D:/Shopping_Support_System/charted_sea_scraper/data/raw_data.csv')
df_neg = pd.read_csv('D:/Shopping_Support_System/charted_sea_scraper/data/raw_data_negative.csv')
common = set(df_pos['itemid'].unique()).intersection(set(df_neg['itemid'].unique()))
if common:
    item_id = list(common)[0]
    print('Picking Shopee item:', item_id)
    neg_reviews = df_neg[df_neg['itemid'] == item_id]
    pos_reviews = df_pos[df_pos['itemid'] == item_id]
    print('Negative reviews count:', len(neg_reviews))
    print('All reviews count earlier:', len(pos_reviews))
