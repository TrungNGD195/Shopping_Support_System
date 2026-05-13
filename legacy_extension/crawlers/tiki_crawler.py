"""
Tiki Reviews Crawler
Crawl reviews từ Tiki.vn bằng API public
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import Optional


class TikiCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        })
        self.base_url = 'https://tiki.vn/api/v2/reviews'
    
    def extract_product_id(self, url: str) -> tuple[Optional[int], Optional[int]]:
        """
        Trích xuất product_id và spid từ URL Tiki
        URL format: https://tiki.vn/ten-san-pham-p{product_id}.html?spid={spid}
        """
        # Extract product_id from URL path
        product_match = re.search(r'-p(\d+)\.html', url)
        product_id = int(product_match.group(1)) if product_match else None
        
        # Extract spid from query params
        spid_match = re.search(r'spid=(\d+)', url)
        spid = int(spid_match.group(1)) if spid_match else None
        
        return product_id, spid
    
    def get_reviews(self, product_id: int, spid: Optional[int] = None, 
                    page: int = 1, limit: int = 20) -> dict:
        """Lấy reviews từ API Tiki"""
        params = {
            'product_id': product_id,
            'limit': limit,
            'page': page,
            'sort': 'score|desc,id|desc,stars|all'  # Sắp xếp theo điểm review
        }
        if spid:
            params['spid'] = spid
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[Tiki] Error fetching reviews: {e}")
            return {}
    
    def crawl_all_reviews(self, url: str, max_reviews: int = 5000) -> dict:
        """
        Crawl tất cả reviews từ một sản phẩm Tiki
        
        Args:
            url: URL sản phẩm Tiki
            max_reviews: Số reviews tối đa cần crawl
            
        Returns:
            dict với thông tin sản phẩm và danh sách reviews
        """
        product_id, spid = self.extract_product_id(url)
        
        if not product_id:
            return {'error': 'Không thể trích xuất product_id từ URL'}
        
        print(f"[Tiki] Crawling product_id={product_id}, spid={spid}")
        
        all_reviews = []
        page = 1
        limit = 20  # Tiki API limit
        total_reviews = 0
        rating_average = 0
        stars_distribution = {}
        
        while len(all_reviews) < max_reviews:
            print(f"[Tiki] Fetching page {page}...")
            data = self.get_reviews(product_id, spid, page, limit)
            
            if not data:
                break
            
            # Lấy thông tin tổng quan từ response đầu tiên
            if page == 1:
                total_reviews = data.get('reviews_count', 0)
                rating_average = data.get('rating_average', 0)
                stars_distribution = data.get('stars', {})
                print(f"[Tiki] Total reviews: {total_reviews}, Rating: {rating_average}")
            
            reviews = data.get('data', [])
            if not reviews:
                print(f"[Tiki] No more reviews at page {page}")
                break
            
            for review in reviews:
                all_reviews.append({
                    'review_id': review.get('id'),
                    'rating_star': review.get('rating'),
                    'title': review.get('title', ''),
                    'comment': review.get('content', ''),
                    'author_username': (review.get('created_by') or {}).get('name', ''),
                    'author_id': review.get('customer_id'),
                    'purchased': (review.get('created_by') or {}).get('purchased', False),
                    'ctime': review.get('created_at'),
                    'date': datetime.fromtimestamp(review.get('created_at', 0)).isoformat() if review.get('created_at') else None,
                    'images': [img.get('full_path') for img in review.get('images', [])],
                    'thank_count': review.get('thank_count', 0),
                    'comment_count': review.get('comment_count', 0),
                })
            
            print(f"[Tiki] Page {page}: +{len(reviews)} reviews, total: {len(all_reviews)}")
            
            # Check if we've got all reviews
            if len(all_reviews) >= total_reviews or len(reviews) < limit:
                break
            
            page += 1
            time.sleep(0.3)  # Rate limiting
        
        result = {
            'platform': 'tiki',
            'product_id': product_id,
            'spid': spid,
            'url': url,
            'total_reviews': total_reviews,
            'rating_average': rating_average,
            'stars_distribution': stars_distribution,
            'crawled_count': len(all_reviews),
            'crawled_at': datetime.now().isoformat(),
            'reviews': all_reviews
        }
        
        print(f"[Tiki] ✅ Hoàn thành! Đã crawl {len(all_reviews)}/{total_reviews} reviews")
        return result
    
    def save_to_json(self, data: dict, filename: Optional[str] = None):
        """Lưu kết quả vào file JSON"""
        if not filename:
            filename = f"tiki_reviews_{data.get('product_id', 'unknown')}_{data.get('spid', '')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[Tiki] Saved to {filename}")
        return filename


# Test
if __name__ == '__main__':
    crawler = TikiCrawler()
    
    # Test URL
    url = "https://tiki.vn/dien-thoai-samsung-galaxy-a26-5g-8-128gb-mat-lung-kinh-ai-circle-to-search-camera-hdr-chup-dem-sang-ro-hang-chinh-hang-p277777809.html?spid=277777815"
    
    result = crawler.crawl_all_reviews(url)
    
    if 'error' not in result:
        crawler.save_to_json(result)
        print(f"\nSummary:")
        print(f"  Total: {result['total_reviews']} reviews")
        print(f"  Crawled: {result['crawled_count']} reviews")
        print(f"  Rating: {result['rating_average']}")
    else:
        print(f"Error: {result['error']}")
