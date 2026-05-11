import os
import json
import csv
import re

INPUT_DIR = "data/reviews"
OUTPUT_FILE = "data/raw_data.csv"

# Các cột output cho team gán nhãn
COLUMNS = [
    "shopid", "itemid", "cmtid", "author_username", "rating_star", "comment",
    "Quality", "Price", "Delivery", "Service"
]

def contains_valid_text(text):
    """
    Kiểm tra xem comment có chứa ít nhất 1 ký tự chữ cái hoặc số hay không.
    (Loại bỏ trường hợp chỉ thả emoji/icon hoặc chuỗi rỗng)
    """
    if not text:
        return False
    # Regex tìm ít nhất 1 chữ cái (bao gồm tiếng Việt) hoặc chữ số
    match = re.search(r'[a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF]', text)
    return match is not None

def export_to_csv():
    all_reviews = []
    
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Directory {INPUT_DIR} does not exist.")
        return

    # Lặp qua các file JSON
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(INPUT_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                reviews = data.get("reviews", [])
                
                for r in reviews:
                    comment = r.get("comment", "").strip()
                    
                    # Bộ lọc: Bỏ comment rỗng và comment chỉ chứa icon
                    if not contains_valid_text(comment):
                        continue
                        
                    # Loại bỏ các ký tự xuống dòng chằng chịt trong comment để CSV gọn gàng hơn
                    comment_clean = " ".join(comment.splitlines())
                    
                    # Tạo row dữ liệu
                    row = {
                        "shopid": r.get("shopid", ""),
                        "itemid": r.get("itemid", ""),
                        "cmtid": r.get("cmtid", ""),
                        "author_username": r.get("author_username", ""),
                        "rating_star": r.get("rating_star", ""),
                        "comment": comment_clean,
                        # Để trống các Aspect để team tự gán nhãn
                        "Quality": "",
                        "Price": "",
                        "Delivery": "",
                        "Service": ""
                    }
                    all_reviews.append(row)
            except Exception as e:
                print(f"[WARN] Failed to process {filename}: {e}")

    # Ghi ra CSV chuẩn utf-8-sig cho Excel
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_reviews)

    print(f"DONE! Đã lọc và xuất thành công {len(all_reviews)} dòng vào file: {OUTPUT_FILE}")

if __name__ == "__main__":
    export_to_csv()
