import pandas as pd
import re
import os

excel_path = "Shopee_Reviews_3h34 (1).xlsx"
pos_csv = "data/positive_reviews.csv"
neg_csv = "data/negative_reviews.csv"

# Load the excel file
df_excel = pd.read_excel(excel_path)

# Prepare lists
positive_rows = []
negative_rows = []

for index, row in df_excel.iterrows():
    link = str(row.get('Link Sản Phẩm', ''))
    rating = row.get('Đánh giá')
    comment = str(row.get('Nội dung', '')).strip()
    
    if not comment or comment == 'nan':
        continue
        
    # Extract product ID
    match = re.search(r'-i\.\d+\.(\d+)', link)
    if match:
        product_id = match.group(1)
    else:
        continue
        
    # Parse rating
    try:
        r = float(rating)
    except:
        r = 5.0 # default if parse fails
        
    new_row = {
        'platform': 'shopee',
        'product_id': product_id,
        'rating': r,
        'comment': comment,
        'Quality': -1,
        'Price': -1,
        'Delivery': -1,
        'Service': -1
    }
    
    if r >= 4:
        positive_rows.append(new_row)
    else:
        negative_rows.append(new_row)

df_pos = pd.DataFrame(positive_rows)
df_neg = pd.DataFrame(negative_rows)

print(f"Found {len(df_pos)} new positive and {len(df_neg)} new negative reviews.")

if not df_pos.empty:
    df_pos.to_csv(pos_csv, mode='a', header=False, index=False, encoding='utf-8-sig')
if not df_neg.empty:
    df_neg.to_csv(neg_csv, mode='a', header=False, index=False, encoding='utf-8-sig')

print("Merged successfully!")
