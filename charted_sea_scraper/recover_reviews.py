import json
import os
import re
import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
BASE_URL = "https://continuous-scraper.common.chartedapi.com/scraping-tasks/shopee"
OUTPUT_DIR = "data/reviews"

def fetch_recent_tasks():
    # Fetch tasks from the last hour
    min_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    
    tasks = []
    limit = 100
    offset = 0
    print(f"Fetching tasks since {min_time}...")
    
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    
    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "includeAllFields": "true",
            "minPendingAt": min_time
        }
        resp = requests.get(BASE_URL, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"Error fetching tasks: {resp.status_code} {resp.text}")
            break
            
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if not items:
            break
            
        print(f"  Fetched {len(items)} tasks at offset {offset}")
        tasks.extend(items)
        offset += limit
        
        # Stop fetching if we're not receiving a full set
        if len(items) < limit:
            break
            
    return tasks

def process_tasks(tasks):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    reviews_by_product = {}
    summaries = {}
    
    for task in tasks:
        if task.get("status") != "SUCCESS":
            continue
            
        url = task.get("url") or task.get("enrichedUrl")
        if not url:
            continue
            
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        
        shopid = qs.get("shopid", [None])[0]
        itemid = qs.get("itemid", [None])[0]
        
        if not shopid or not itemid:
            continue
            
        key = (shopid, itemid)
        if key not in reviews_by_product:
            reviews_by_product[key] = []
            
        body = task.get("responseBody")
        if not body:
            continue
            
        try:
            b_data = json.loads(body) if isinstance(body, str) else body
            r_data = b_data.get("data", {})
            ratings = r_data.get("ratings", [])
            
            for r in ratings:
                review = {
                    "cmtid": r.get("cmtid"),
                    "itemid": r.get("itemid"),
                    "shopid": r.get("shopid"),
                    "rating_star": r.get("rating_star"),
                    "comment": r.get("comment", ""),
                    "author_username": r.get("author_username", ""),
                    "ctime": r.get("ctime"),
                    "images": r.get("images", []),
                    "videos": [v.get("id") for v in r.get("videos", [])],
                }
                reviews_by_product[key].append(review)
                
            rs = r_data.get("item_rating_summary")
            if rs and key not in summaries:
                summaries[key] = rs
                
        except Exception as e:
            print(f"Error parsing task {task.get('uuid')}: {e}")

    # Remove duplicates from each list
    for key in reviews_by_product:
        unique_reviews = {r["cmtid"]: r for r in reviews_by_product[key]}.values()
        reviews_by_product[key] = list(unique_reviews)

    print("\n--- Summary ---")
    for (shopid, itemid), revs in reviews_by_product.items():
        if len(revs) > 0:
            out_file = os.path.join(OUTPUT_DIR, f"reviews_{shopid}_{itemid}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({
                    "product": {"shopid": shopid, "itemid": itemid},
                    "rating_summary": summaries.get((shopid, itemid), {}),
                    "total_reviews_crawled": len(revs),
                    "reviews": revs
                }, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(revs):4d} reviews matching product {itemid} to {out_file}")

if __name__ == "__main__":
    t = fetch_recent_tasks()
    process_tasks(t)
