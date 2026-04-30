"""
Test: Crawl product page directly via Charted Sea API.
The scraper should extract product details including reviews from the product page.
"""
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
BASE_URL = "https://continuous-scraper.common.chartedapi.com/scraping-tasks"

# Test with the product page URL in the standard -i.shopid.itemid format
test_url = "https://shopee.vn/api/v4/item_rating/get_item_rating_list?itemid=28359011110&shopid=1316099166&type=0&offset=0&limit=6"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

body = {
    "requests": [
        {"url": test_url}
    ],
    "cacheMaxAgeInSec": 3600
}

params = {
    "waitForCompletion": "true",
    "autoCancelAfterSec": 600,
    "includeAllFields": "true"
}

print(f"Sending product page URL: {test_url}")
print("Waiting for Charted Sea to scrape...")

response = requests.post(
    f"{BASE_URL}/shopee/run",
    headers=headers,
    json=body,
    params=params,
    timeout=660
)

print(f"Status code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/test_product_page_response.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Response saved. Tasks: {len(result)}")
    
    if isinstance(result, list) and len(result) > 0:
        task = result[0]
        print(f"Task status: {task.get('status')}")
        print(f"Known API: {task.get('knownApi')}")
        print(f"Enriched URL: {(task.get('enrichedUrl') or '')[:150]}")
        
        resp_body = task.get('responseBody')
        if resp_body:
            try:
                body_data = json.loads(resp_body) if isinstance(resp_body, str) else resp_body
                if isinstance(body_data, dict):
                    print(f"Response body top-level keys: {list(body_data.keys())}")
                    # Check for item_rating or ratings
                    for key in ['item_rating', 'ratings', 'data', 'item']:
                        if key in body_data:
                            sub = body_data[key]
                            if isinstance(sub, dict):
                                print(f"  '{key}' keys: {list(sub.keys())}")
                            elif isinstance(sub, list):
                                print(f"  '{key}' has {len(sub)} items")
                    
                    # Print first 2000 chars to inspect structure
                    body_str = json.dumps(body_data, ensure_ascii=False, indent=2)
                    print(f"\n--- Response body preview (first 3000 chars) ---")
                    print(body_str[:3000])
                else:
                    print(f"Response body type: {type(body_data)}")
                    print(str(body_data)[:2000])
            except json.JSONDecodeError:
                print(f"responseBody is not JSON: {str(resp_body)[:2000]}")
        else:
            print(f"Error message: {task.get('errorMessage', 'N/A')}")
else:
    print(f"Error: {response.text[:500]}")
