import requests
import json
import csv
import time

categories = {
    'fashion': 'thời trang',
    'electronics': 'điện tử',
    'beauty': 'làm đẹp',
    'home': 'nhà cửa',
    'mother-baby': 'mẹ và bé',
    'other': 'sách'
}

req_counts = {
    'fashion': 3,
    'electronics': 3,
    'beauty': 3,
    'home': 3,
    'mother-baby': 3,
    'other': 2
}

results = []

for cat, query in categories.items():
    collected = 0
    page = 1
    while collected < req_counts[cat] and page <= 20:
        url = f'https://tiki.vn/api/v2/products?limit=50&q={query}&page={page}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = requests.get(url, headers=headers)
            data = r.json().get('data', [])
            if not data:
                break
            for item in data:
                reviews = item.get('review_count', 0)
                if 500 <= reviews <= 5000: # Lowered threshold to 500 for Tiki just in case
                    product_url = 'https://tiki.vn/' + item.get('url_path', '')
                    # avoid duplicates
                    if product_url not in [x['url'] for x in results]:
                        results.append({'platform': 'tiki', 'category': cat, 'url': product_url})
                        collected += 1
                        if collected >= req_counts[cat]:
                            break
            page += 1
            time.sleep(0.5)
        except Exception as e:
            break
            
print(f"Collected {len(results)} Tiki URLs")
with open('tiki_urls.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
