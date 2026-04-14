"""
Crawl product review details from Shopee using Charted Sea API.
Uses /api/v2/item/get_ratings with auto-pagination.
Submits all products in batches, polls for completion, saves to data/reviews/.
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
OUTPUT_DIR = "data/reviews"
REVIEW_API_TEMPLATE = "https://shopee.vn/api/v2/item/get_ratings?shopid={shopid}&itemid={itemid}&limit=6&offset=0&type=0&filter=0"

MAX_PAGES = 500
MAX_RESULTS = 3000
PAGE_SIZE = 50
BATCH_SIZE = 5  # Products per API batch call


def parse_shopee_url(url):
    url = url.strip().strip('"')
    match = re.search(r'/product/(\d+)/(\d+)', url)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.search(r'-i\.(\d+)\.(\d+)', url)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def read_urls_from_csv(csv_path):
    products = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('product_url', '').strip().strip('"')
            if not url:
                continue
            shopid, itemid = parse_shopee_url(url)
            if shopid and itemid:
                products.append({
                    'id': row.get('id'),
                    'platform': row.get('platform'),
                    'category': row.get('category'),
                    'original_url': url,
                    'shopid': shopid,
                    'itemid': itemid,
                    'note': row.get('note', '')
                })
    return products


def submit_batch(api_urls):
    """Submit a batch of scraping tasks using the /run endpoint (async)."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    body = {
        "requests": [{"url": u} for u in api_urls],
        "cacheMaxAgeInSec": 3600,
        "productRatings_enrichUrlQuery_pageSize": PAGE_SIZE,
        "productRatings_crawlNextPages": True,
        "productRatings_crawlNextPages_maxPages": MAX_PAGES,
        "productRatings_crawlNextPages_maxResults": MAX_RESULTS,
        "productRatings_autofixError10002": True
    }
    params = {"waitForCompletion": "false", "autoCancelAfterSec": 1200}

    resp = requests.post(f"{BASE_URL}/{SCRAPER}/run", headers=headers, json=body, params=params, timeout=30)
    if resp.status_code == 200:
        result = resp.json()
        if isinstance(result, list):
            return [t.get("uuid") for t in result if t.get("uuid")]
        return []
    else:
        print(f"    [ERROR] {resp.status_code}: {resp.text[:300]}")
        return []


def poll_all_tasks(root_uuids, max_wait=900):
    """Poll until all root tasks reach terminal status, then fetch all tasks."""
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    url = f"{BASE_URL}/{SCRAPER}"
    start = time.time()

    while time.time() - start < max_wait:
        # Fetch root tasks in chunks (API limit)
        all_root_tasks = []
        for i in range(0, len(root_uuids), 20):
            chunk = root_uuids[i:i+20]
            resp = requests.get(url, headers=headers, params={
                "uuids": ",".join(chunk), "includeAllFields": "false", "limit": 100
            }, timeout=30)
            if resp.status_code == 200:
                all_root_tasks.extend(resp.json())

        pending = 0
        for t in all_root_tasks:
            if isinstance(t, dict):
                if t.get("status") in ("PENDING", "RUNNING", "BLOCKED", "ERROR"):
                    pending += 1
            else:
                print(f"    [WARN] Unexpected task format: {t}")
        done = len(all_root_tasks) - pending

        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] Root tasks: {done} done, {pending} pending")

        if pending == 0:
            break
        time.sleep(15)

    # Now fetch ALL tasks with full data (root + children)
    print("  Fetching full results with responseBody...")
    all_tasks = []
    for i in range(0, len(root_uuids), 10):
        chunk = root_uuids[i:i+10]
        resp = requests.get(url, headers=headers, params={
            "uuids": ",".join(chunk), "includeAllFields": "true", "limit": 200
        }, timeout=60)
        if resp.status_code == 200:
            all_tasks.extend(resp.json())
        time.sleep(1)

    return all_tasks


def extract_reviews(tasks):
    """Extract clean reviews from completed tasks."""
    all_reviews = []
    summary = None
    for task in tasks:
        if task.get("status") != "SUCCESS":
            continue
        resp_body = task.get("responseBody")
        if not resp_body:
            continue
        try:
            data = json.loads(resp_body) if isinstance(resp_body, str) else resp_body
            ratings = data.get("data", {}).get("ratings", [])
            for r in ratings:
                review = {
                    "cmtid": r.get("cmtid"),
                    "itemid": r.get("itemid"),
                    "shopid": r.get("shopid"),
                    "rating_star": r.get("rating_star"),
                    "comment": r.get("comment", ""),
                    "author_username": r.get("author_username", ""),
                    "anonymous": r.get("anonymous", False),
                    "ctime": r.get("ctime"),
                    "images": r.get("images", []),
                    "videos": [v.get("id") for v in r.get("videos", [])],
                    "like_count": r.get("like_count", 0),
                    "detailed_rating": r.get("detailed_rating", {}),
                    "template_tags": r.get("template_tags", []),
                    "product_name": (r.get("product_items") or [{}])[0].get("name", ""),
                    "model_name": (r.get("product_items") or [{}])[0].get("model_name", ""),
                }
                all_reviews.append(review)
            rs = data.get("data", {}).get("item_rating_summary")
            if rs and not summary:
                summary = rs
        except Exception as e:
            pass
    return all_reviews, summary


def main():
    print("=" * 60)
    print("Shopee Review Crawler — Full Crawl (Async)")
    print(f"  Pagination: max {MAX_PAGES} pages / {MAX_RESULTS} results per product")
    print(f"  Output: {OUTPUT_DIR}/")
    print("=" * 60)

    if not BEARER_TOKEN:
        print("[ERROR] No BEARER_TOKEN!")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    products = read_urls_from_csv("url_collection.csv")
    print(f"\n[INFO] {len(products)} products to crawl\n")

    # Build API URLs and map them to products
    api_urls = []
    url_to_product = {}
    for prod in products:
        api_url = REVIEW_API_TEMPLATE.format(shopid=prod['shopid'], itemid=prod['itemid'])
        api_urls.append(api_url)
        url_to_product[api_url] = prod

    # Phase 1: Submit in batches
    print("PHASE 1: Submitting tasks")
    print("-" * 40)
    all_root_uuids = []
    uuid_to_product = {}

    for i in range(0, len(api_urls), BATCH_SIZE):
        batch = api_urls[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(api_urls) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} products)...")

        uuids = submit_batch(batch)
        for j, uuid in enumerate(uuids):
            if i + j < len(api_urls):
                all_root_uuids.append(uuid)
                uuid_to_product[uuid] = url_to_product[api_urls[i + j]]

        print(f"    -> Got {len(uuids)} UUIDs")
        time.sleep(2)

    print(f"\n[INFO] Submitted {len(all_root_uuids)} root tasks\n")

    # Phase 2: Poll
    print("PHASE 2: Waiting for completion")
    print("-" * 40)
    all_tasks = poll_all_tasks(all_root_uuids, max_wait=900)
    print(f"\n[INFO] Retrieved {len(all_tasks)} total tasks (incl. paginated sub-tasks)\n")

    # Group tasks by root UUID  
    # Each root task spawns child tasks for subsequent pages
    task_groups = {}
    for task in all_tasks:
        root = task.get("parentUuid") or task.get("uuid")
        if root not in task_groups:
            task_groups[root] = []
        task_groups[root].append(task)

    # Phase 3: Extract & save
    print("PHASE 3: Saving reviews")
    print("-" * 40)
    total_reviews = 0
    results = []

    for uuid in all_root_uuids:
        prod = uuid_to_product.get(uuid, {})
        tasks_for_product = task_groups.get(uuid, [])
        reviews, summary = extract_reviews(tasks_for_product)

        outfile = os.path.join(OUTPUT_DIR, f"reviews_{prod.get('shopid')}_{prod.get('itemid')}.json")
        out = {
            "product": {
                "shopid": prod.get("shopid"),
                "itemid": prod.get("itemid"),
                "category": prod.get("category"),
                "original_url": prod.get("original_url"),
                "note": prod.get("note")
            },
            "rating_summary": summary,
            "total_reviews_crawled": len(reviews),
            "reviews": reviews
        }
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

        total_reviews += len(reviews)
        mark = "✓" if reviews else "✗"
        print(f"  {mark} {prod.get('itemid')}: {len(reviews)} reviews")
        results.append({
            "shopid": prod.get("shopid"),
            "itemid": prod.get("itemid"),
            "category": prod.get("category"),
            "reviews_crawled": len(reviews),
            "total_ratings": summary.get("rating_total", 0) if summary else 0
        })

    # Summary
    with open(os.path.join(OUTPUT_DIR, "_crawl_summary.json"), 'w', encoding='utf-8') as f:
        json.dump({
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_products": len(products),
            "total_reviews": total_reviews,
            "products": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"DONE! {total_reviews} reviews from {len(all_root_uuids)} products")
    print(f"Saved to: {OUTPUT_DIR}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
