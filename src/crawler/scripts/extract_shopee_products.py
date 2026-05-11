import json
import csv
import glob
import os

RAW_DIR = "data/raw"
CSV_PATH = "data/products.csv"

def get_flash_products():
    path = os.path.join(RAW_DIR, "flash.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products = []
    items = data.get("data", {}).get("items", [])
    for item in items:
        rating = item.get("item_rating")
        if rating and "rating_counts" in rating:
            total = rating["rating_counts"][0]
            if 1000 <= total <= 20000:
                shopid = item.get("shopid")
                itemid = item.get("itemid")
                if shopid and itemid:
                    products.append(f"https://shopee.vn/product/{shopid}/{itemid}")
    return products

def get_standard_products(filename):
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products = []
    units = data.get("data", {}).get("units", [])
    for u in units:
        item = u.get("item")
        if item and "item_data" in item:
            item_data = item["item_data"]
            rating = item_data.get("item_rating")
            if rating and "rating_count" in rating:
                counts = rating["rating_count"]
                total = counts[0] if isinstance(counts, list) else 0
                if 1000 <= total <= 20000:
                    shopid = item_data.get("shopid")
                    itemid = item_data.get("itemid")
                    if shopid and itemid:
                        products.append(f"https://shopee.vn/product/{shopid}/{itemid}")
    return products

def main():
    print("Loading valid products from raw JSON files...")
    categories_from_standard = {
        "fashion": get_standard_products("fashion.json"),
        "electronics": get_standard_products("electronics.json"),
        "beauty": get_standard_products("beauty.json"),
        "mother-baby": get_standard_products("mother-baby.json")
    }
    flash_products = get_flash_products()
    
    print(f"Loaded from flash.json: {len(flash_products)}")
    for k, v in categories_from_standard.items():
        print(f"Loaded from {k}.json: {len(v)}")
        
    # Read the CSV
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
        
    print(f"\nUpdating {CSV_PATH}...")
    used_flash_idx = 0
    updated_count = 0
    
    for row in rows:
        if row["platform"] != "shopee":
            continue
            
        cat = row["category"]
        new_url = None
        
        # Determine source of product URL
        if cat in categories_from_standard:
            pool = categories_from_standard[cat]
            if len(pool) > 0:
                new_url = pool.pop(0)
        elif cat in ["home", "other"]:
            if used_flash_idx < len(flash_products):
                new_url = flash_products[used_flash_idx]
                used_flash_idx += 1
                
        if new_url:
            row["product_url"] = new_url
            updated_count += 1
            
    # Write back to CSV
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Updated {updated_count} shopee product URLs in {CSV_PATH}.")

if __name__ == "__main__":
    main()
