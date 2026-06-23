import csv
import os
import time
import random
import re
import pandas as pd
import sys

try:
    from src.crawler.scripts.realtime_shopee import ShopeeCrawler
    from src.crawler.scripts.realtime_tiki import TikiCrawler
except ImportError:
    pass

def _extract_product_id(url: str) -> str | None:
    """Extract product_id from a Shopee or Tiki URL."""
    m = re.search(r'i\.(\d+)\.(\d+)', url)
    if m:
        return m.group(2)
    m = re.search(r'(?:i|p-?)(\d{6,})', url)
    if m:
        return m.group(1)
    numbers = re.findall(r'(\d{6,})', url)
    if numbers:
        return numbers[-1]
    return None

def get_reviews_from_url(url: str) -> list[str]:
    """
    Scraper Real-time: Thu thập bình luận trực tiếp từ API của Tiki và Shopee.
    Dữ liệu sẽ được cào mới hoàn toàn khi người dùng nhập link.
    """
    comments = []
    
    if "tiki.vn" in url.lower():
        try:
            crawler = TikiCrawler()
            result = crawler.crawl_all_reviews(url, max_reviews=150)
            if 'error' not in result and 'reviews' in result:
                for rv in result['reviews']:
                    c = str(rv.get('comment', '')).strip()
                    if len(c) > 5:
                        comments.append(c)
        except Exception as e:
            print(f"[Scraper] Lỗi đọc dữ liệu Tiki real-time: {e}")

    elif "shopee.vn" in url.lower():
        try:
            crawler = ShopeeCrawler()
            _, reviews = crawler.crawl_from_url(url, max_reviews=150)
            if reviews:
                for rv in reviews:
                    c = str(rv.get('comment', '')).strip()
                    if len(c) > 5:
                        comments.append(c)
        except Exception as e:
            print(f"[Scraper] Lỗi đọc dữ liệu Shopee real-time: {e}")

    if not comments:
        print("[Scraper] Cảnh báo: Không crawl được dữ liệu hợp lệ nào từ URL này.")
        return []
    
    random.shuffle(comments)
    return comments
