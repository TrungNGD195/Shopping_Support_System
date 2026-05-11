"""
Crawl negative reviews (1, 2, 3 stars) from Shopee using Charted Sea API.
Uses /api/v2/item/get_ratings with type=1, type=2, type=3.
"""
import csv
import json
import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
BASE_URL = "https://continuous-scraper.common.chartedapi.com/scraping-tasks"
SCRAPER = "shopee"
OUTPUT_DIR = "data/negative_reviews"
CSV_OUT = "data/raw_data_negative.csv"

# template with {rating_type} ranging from 1 to 3
REVIEW_API_TEMPLATE = "https://shopee.vn/api/v2/item/get_ratings?shopid={shopid}&itemid={itemid}&limit=50&offset=0&type={rating_type}&filter=0"

PAGE_SIZE = 50
BATCH_SIZE = 10

def parse_shopee_url(url):
    url = url.strip().strip('"')
    match = re.search(r'/product/(\d+)/(\d+)', url)
    if match: return int(match.group(1)), int(match.group(2))
    match = re.search(r'-i\.(\d+)\.(\d+)', url)
    if match: return int(match.group(1)), int(match.group(2))
    return None, None

def read_urls_from_csv(csv_path):
    products = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('product_url', '').strip().strip('"')
            if not url: continue
            shopid, itemid = parse_shopee_url(url)
            if shopid and itemid:
                products.append({
                    'shopid': shopid,
                    'itemid': itemid,
                })
    return products

def submit_batch(api_urls):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BEARER_TOKEN}"}
    body = {
        "requests": [{"url": u} for u in api_urls],
        "cacheMaxAgeInSec": 3600,
        "productRatings_enrichUrlQuery_pageSize": PAGE_SIZE,
        "productRatings_crawlNextPages": True,
        "productRatings_crawlNextPages_maxPages": 20, # Low stars usually don't need 500 pages
        "productRatings_crawlNextPages_maxResults": 1000,
        "productRatings_autofixError10002": True
    }
    params = {"waitForCompletion": "false", "autoCancelAfterSec": 1200}
    resp = requests.post(f"{BASE_URL}/{SCRAPER}/run", headers=headers, json=body, params=params, timeout=30)
    if resp.status_code == 200:
        result = resp.json()
        if isinstance(result, list):
            return [t.get("uuid") for t in result if t.get("uuid")]
    else:
        print(f"    [ERROR] {resp.status_code}: {resp.text[:300]}")
    return []

def poll_all_tasks(root_uuids, max_wait=900):
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    url = f"{BASE_URL}/{SCRAPER}"
    start = time.time()
    while time.time() - start < max_wait:
        all_root_tasks = []
        for i in range(0, len(root_uuids), 20):
            chunk = root_uuids[i:i+20]
            resp = requests.get(url, headers=headers, params={"uuids": ",".join(chunk), "includeAllFields": "false", "limit": 100}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", data) if isinstance(data, dict) else data
                all_root_tasks.extend(items)
        
        pending = 0
        for t in all_root_tasks:
            if isinstance(t, dict) and t.get("status") in ("PENDING", "RUNNING", "BLOCKED", "ERROR"):
                pending += 1
        done = len(all_root_tasks) - pending
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] Root tasks: {done} done, {pending} pending")
        if pending == 0: break
        time.sleep(15)

    print("  Fetching full results with responseBody...")
    all_tasks = []
    for i in range(0, len(root_uuids), 10):
        chunk = root_uuids[i:i+10]
        resp = requests.get(url, headers=headers, params={"uuids": ",".join(chunk), "includeAllFields": "true", "limit": 200}, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            all_tasks.extend(items)
        time.sleep(1)
    return all_tasks

def contains_valid_text(text):
    if not text: return False
    return re.search(r'[a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF]', text) is not None

def extract_and_save_reviews(all_tasks, uuid_to_meta):
    task_groups = {}
    for task in all_tasks:
        if not isinstance(task, dict): continue
        root = task.get("parentUuid") or task.get("uuid")
        if root not in task_groups: task_groups[root] = []
        task_groups[root].append(task)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_rows = []
    total_reviews = 0

    for uuid, meta in uuid_to_meta.items():
        shopid = meta['shopid']
        itemid = meta['itemid']
        rating_type = meta['rating_type']
        
        tasks_for_prod = task_groups.get(uuid, [])
        for task in tasks_for_prod:
            if task.get("status") != "SUCCESS": continue
            resp_body = task.get("responseBody")
            if not resp_body: continue
            try:
                data = json.loads(resp_body) if isinstance(resp_body, str) else resp_body
                ratings = data.get("data", {}).get("ratings", [])
                for r in ratings:
                    comment = r.get("comment", "").strip()
                    if not contains_valid_text(comment): continue
                    
                    comment_clean = " ".join(comment.splitlines())
                    
                    row = {
                        "shopid": r.get("shopid", shopid),
                        "itemid": r.get("itemid", itemid),
                        "cmtid": r.get("cmtid", ""),
                        "author_username": r.get("author_username", ""),
                        "rating_star": r.get("rating_star", rating_type),
                        "comment": comment_clean,
                        "Quality": "", "Price": "", "Delivery": "", "Service": ""
                    }
                    csv_rows.append(row)
            except Exception as e:
                pass

    # Save to CSV
    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    # Deduplicate based on cmtid in case of overlaps
    unique_reviews = {}
    for r in csv_rows:
        if r["cmtid"] not in unique_reviews:
            unique_reviews[r["cmtid"]] = r
    
    final_rows = list(unique_reviews.values())
    
    with open(CSV_OUT, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["shopid", "itemid", "cmtid", "author_username", "rating_star", "comment", "Quality", "Price", "Delivery", "Service"])
        writer.writeheader()
        writer.writerows(final_rows)
        
    return len(final_rows)

def main():
    if not BEARER_TOKEN:
        print("[ERROR] No BEARER_TOKEN!")
        return

    products = read_urls_from_csv("url_collection.csv")
    api_urls = []
    url_to_meta = {}
    
    for prod in products:
        for r_type in [1, 2, 3]:
            api_url = REVIEW_API_TEMPLATE.format(shopid=prod['shopid'], itemid=prod['itemid'], rating_type=r_type)
            api_urls.append(api_url)
            url_to_meta[api_url] = {"shopid": prod['shopid'], "itemid": prod['itemid'], "rating_type": r_type}

    print(f"[INFO] 30 products * 3 types = {len(api_urls)} tasks to submit")

    all_root_uuids = []
    uuid_to_meta = {}

    for i in range(0, len(api_urls), BATCH_SIZE):
        batch = api_urls[i:i+BATCH_SIZE]
        uuids = submit_batch(batch)
        for j, uuid in enumerate(uuids):
            all_root_uuids.append(uuid)
            uuid_to_meta[uuid] = url_to_meta[api_urls[i + j]]
        print(f"  Submitted batch {i//BATCH_SIZE + 1} -> got {len(uuids)} UUIDs")
        time.sleep(2)

    print(f"\n[INFO] Submitted {len(all_root_uuids)} root tasks. Waiting for completion...")
    all_tasks = poll_all_tasks(all_root_uuids, max_wait=900)
    
    print("\n[INFO] Extracting reviews to CSV...")
    total_extracted = extract_and_save_reviews(all_tasks, uuid_to_meta)
    
    print(f"\n{'=' * 60}")
    print(f"DONE! Crawled strictly 1-3 star reviews.")
    print(f"Extracted {total_extracted} valid low-star reviews to: {CSV_OUT}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
