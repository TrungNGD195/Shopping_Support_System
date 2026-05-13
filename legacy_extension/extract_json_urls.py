import json
import csv

input_json = "data/raw/momnbaby.json"
output_csv = "url_collection.csv"

# Read the template simply to get the header structure
template_file = "url_collection_template.csv"
header = ["id", "platform", "category", "product_url", "priority", "status", "note"]

try:
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error reading JSON: {e}")
    exit(1)

matching_products = []

# Process the JSON structure
units = data.get("data", {}).get("units", [])
for unit in units:
    item_data = unit.get("item", {}).get("item_data", {})
    if not item_data:
        continue
        
    rating_info = item_data.get("item_rating", {})
    rating_count_arr = rating_info.get("rating_count", [0])
    
    total_reviews = rating_count_arr[0] if rating_count_arr else 0
    
    # Check if reviews are between 1000 and 10000
    if 1000 <= total_reviews <= 10000:
        shopid = item_data.get("shopid")
        itemid = item_data.get("itemid")
        
        if shopid and itemid:
            url = f"https://shopee.vn/product/{shopid}/{itemid}"
            
            # Use 'unknown' category as we don't have a specific mapping from catid
            # You could add mapping logic if you know what catid 100013 represents
            product = {
                "platform": "shopee",
                "category": "", 
                "url": f'"{url}"',
                "reviews": total_reviews
            }
            matching_products.append(product)

print(f"Found {len(matching_products)} products with 1000-10000 reviews.")

# Write to CSV
try:
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for idx, prod in enumerate(matching_products, 1):
            writer.writerow([
                idx,
                prod["platform"],
                prod["category"],
                prod["url"],
                "high",
                "pending",
                f"{prod['reviews']} reviews"
            ])
    print(f"Successfully saved {len(matching_products)} URLs to {output_csv}")
except Exception as e:
    print(f"Error writing CSV: {e}")
