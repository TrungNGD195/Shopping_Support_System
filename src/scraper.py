import csv
import os
import re
import random

# Cache reviews indexed by product_id at module load
_REVIEWS = {}

def _load_reviews():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    for filename in ("positive_reviews.csv", "negative_reviews.csv"):
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                pid = row.get("product_id", "").strip()
                comment = row.get("comment", "").strip()
                if pid and comment:
                    _REVIEWS.setdefault(pid, []).append(comment)

_load_reviews()

def _extract_product_id(url: str) -> str | None:
    """Extract product_id from a Shopee or Tiki URL."""
    # Shopee: ...i.{shop_id}.{product_id} or ...-i.{shop_id}.{product_id}
    m = re.search(r'i\.(\d+)\.(\d+)', url)
    if m:
        return m.group(2)
    # Tiki: ...i{product_id} or ...p-{product_id}
    m = re.search(r'(?:i|p-?)(\d{6,})', url)
    if m:
        return m.group(1)
    # Fallback: last long number in URL
    numbers = re.findall(r'(\d{6,})', url)
    if numbers:
        return numbers[-1]
    return None

def get_reviews_from_url(url: str) -> list[str]:
    """Lấy bình luận từ CSV theo product_id trong URL."""
    pid = _extract_product_id(url)
    if pid and pid in _REVIEWS:
        reviews = _REVIEWS[pid]
        random.shuffle(reviews)
        return reviews[:min(len(reviews), 50)]

    # Fallback: random sample from all reviews if product not found
    all_reviews = [c for cs in _REVIEWS.values() for c in cs]
    if all_reviews:
        random.shuffle(all_reviews)
        return all_reviews[:random.randint(5, 8)]

    return []
