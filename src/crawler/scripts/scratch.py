import json
import glob

files = glob.glob('data/raw/*.json')
for fpath in files:
    with open(fpath) as f:
        data = json.load(f)
    print(fpath)
    items = data.get('data', {}).get('items', [])
    if isinstance(data, list):
         items = data
    if items:
        for i, item in enumerate(items[:2]):
            basic = item.get('item_basic', {})
            sold = basic.get('historical_sold')
            rating = basic.get('item_rating')
            name = basic.get('name')
            name_str = name[:30] if name else str(name)
            rating_count = rating.get('rating_count') if rating else None
            print(f"  Item {i}: name: {name_str} | sold: {sold} | rating_count: {rating_count}")
