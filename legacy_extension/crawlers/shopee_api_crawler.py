"""
Shopee Reviews Crawler - API Version
Crawl đánh giá từ Shopee qua API công khai, không cần login
"""

import requests
import pandas as pd
import json
import re
import time
from datetime import datetime
from typing import Optional


class ShopeeCrawler:
    """Crawler lấy reviews từ Shopee qua API"""
    
    def __init__(self):
        self.session = requests.Session()
        # Headers giống browser thật
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        })
    
    def extract_ids_from_url(self, url: str) -> tuple[Optional[int], Optional[int]]:
        """Trích xuất shop_id và item_id từ URL Shopee"""
        pattern = r'i\.(\d+)\.(\d+)'
        match = re.search(pattern, url)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None
    
    def _init_session(self, shop_id: int, item_id: int):
        """Khởi tạo session bằng cách truy cập trang sản phẩm trước"""
        # Truy cập trang sản phẩm để lấy cookies
        product_url = f"https://shopee.vn/product/{shop_id}/{item_id}"
        
        try:
            # Set referer
            self.session.headers["Referer"] = product_url
            
            # Lấy cookies từ trang chủ
            self.session.get("https://shopee.vn/", timeout=10)
            time.sleep(1)
            
        except Exception as e:
            print(f"Warning: Không thể init session: {e}")
    
    def get_product_info(self, shop_id: int, item_id: int) -> dict:
        """Lấy thông tin sản phẩm"""
        url = "https://shopee.vn/api/v2/item/get"
        params = {
            "itemid": item_id,
            "shopid": shop_id,
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("item"):
                    item = data["item"]
                    return {
                        "name": item.get("name", ""),
                        "shop_id": shop_id,
                        "item_id": item_id,
                        "rating_star": item.get("item_rating", {}).get("rating_star", 0),
                        "rating_count": sum(item.get("item_rating", {}).get("rating_count", [0])),
                        "price": item.get("price", 0) / 100000,
                        "sold": item.get("historical_sold", 0),
                    }
        except Exception as e:
            print(f"Lỗi lấy thông tin sản phẩm: {e}")
        
        return {"shop_id": shop_id, "item_id": item_id}
    
    def crawl_reviews(self, shop_id: int, item_id: int, max_reviews: int = 200) -> list[dict]:
        """
        Crawl reviews qua API
        
        Args:
            shop_id: ID shop
            item_id: ID sản phẩm
            max_reviews: Số reviews tối đa cần lấy
        """
        url = "https://shopee.vn/api/v2/item/get_ratings"
        all_reviews = []
        offset = 0
        limit = 50  # Max 50 per request
        
        print(f"Bắt đầu crawl reviews cho item {item_id}...")
        
        while len(all_reviews) < max_reviews:
            params = {
                "filter": 0,  # 0=tất cả, 1-5=theo số sao
                "flag": 1,
                "itemid": item_id,
                "limit": limit,
                "offset": offset,
                "shopid": shop_id,
                "type": 0,
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=15)
                
                if resp.status_code != 200:
                    print(f"HTTP {resp.status_code}")
                    break
                
                data = resp.json()
                
                # Check error
                if data.get("error"):
                    print(f"API Error: {data.get('error_msg', 'Unknown')}")
                    break
                
                ratings = data.get("data", {}).get("ratings", [])
                
                if not ratings:
                    print("Đã hết reviews")
                    break
                
                for r in ratings:
                    review = self._parse_review(r)
                    all_reviews.append(review)
                
                print(f"  Offset {offset}: Lấy {len(ratings)} reviews (Tổng: {len(all_reviews)})")
                
                offset += limit
                time.sleep(0.5)  # Rate limit
                
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                break
            except json.JSONDecodeError:
                print("JSON decode error")
                break
        
        print(f"Hoàn thành! Tổng: {len(all_reviews)} reviews")
        return all_reviews
    
    def _parse_review(self, r: dict) -> dict:
        """Parse review từ API response"""
        ctime = r.get("ctime", 0)
        comment_date = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S") if ctime else ""
        
        # Lấy variant/model
        product_items = ""
        items = r.get("product_items", [])
        if items:
            product_items = ", ".join([i.get("model_name", "") for i in items if i.get("model_name")])
        
        return {
            "rating_star": r.get("rating_star", 0),
            "comment": r.get("comment", ""),
            "comment_date": comment_date,
            "username": r.get("author_username", ""),
            "product_items": product_items,
            "likes": r.get("like_count", 0),
            "has_images": len(r.get("images", [])) > 0,
            "has_video": len(r.get("videos", [])) > 0,
        }
    
    def crawl_from_url(self, url: str, max_reviews: int = 200) -> tuple[dict, list[dict]]:
        """Crawl từ URL sản phẩm"""
        shop_id, item_id = self.extract_ids_from_url(url)
        
        if not shop_id or not item_id:
            raise ValueError(f"URL không hợp lệ: {url}")
        
        print(f"Shop ID: {shop_id}, Item ID: {item_id}")
        
        # Init session
        self._init_session(shop_id, item_id)
        
        # Lấy thông tin sản phẩm
        product_info = self.get_product_info(shop_id, item_id)
        if product_info.get("name"):
            print(f"Sản phẩm: {product_info['name'][:50]}...")
        
        # Crawl reviews
        reviews = self.crawl_reviews(shop_id, item_id, max_reviews)
        
        return product_info, reviews
    
    def save_to_csv(self, reviews: list[dict], filename: str):
        """Lưu ra file CSV"""
        if not reviews:
            print("Không có reviews để lưu")
            return
        df = pd.DataFrame(reviews)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"Đã lưu {len(reviews)} reviews vào {filename}")
    
    def save_to_json(self, product_info: dict, reviews: list[dict], filename: str):
        """Lưu ra file JSON"""
        data = {
            "product_info": product_info,
            "reviews": reviews,
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_reviews": len(reviews)
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu vào {filename}")


if __name__ == "__main__":
    import os
    
    print("="*50)
    print("SHOPEE REVIEWS CRAWLER (API Version)")
    print("="*50)
    
    # Test với URL
    test_url = input("Nhập URL sản phẩm Shopee: ").strip()
    
    if test_url:
        crawler = ShopeeCrawler()
        
        try:
            product_info, reviews = crawler.crawl_from_url(test_url, max_reviews=100)
            
            if reviews:
                os.makedirs("data/raw", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                crawler.save_to_csv(reviews, f"data/raw/reviews_{timestamp}.csv")
                crawler.save_to_json(product_info, reviews, f"data/raw/reviews_{timestamp}.json")
                
                # Thống kê
                print("\n" + "="*50)
                print("THỐNG KÊ")
                print("="*50)
                df = pd.DataFrame(reviews)
                print(f"Tổng reviews: {len(df)}")
                print(f"Có comment: {len(df[df['comment'] != ''])}")
                print(f"\nPhân bố đánh giá:")
                for star in range(5, 0, -1):
                    count = len(df[df['rating_star'] == star])
                    print(f"  {star}⭐: {count}")
                    
                # Hiển thị mẫu
                print("\n--- MẪU REVIEWS ---")
                for i, r in enumerate(reviews[:3]):
                    print(f"\n[{i+1}] {r['rating_star']}⭐ - {r['username']}")
                    print(f"    {r['comment'][:100]}..." if len(r['comment']) > 100 else f"    {r['comment']}")
            else:
                print("Không lấy được reviews!")
                
        except Exception as e:
            print(f"Lỗi: {e}")
            import traceback
            traceback.print_exc()
