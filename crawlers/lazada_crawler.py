"""
Lazada Reviews Crawler
Crawl reviews từ Lazada.vn bằng API public
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import Optional


class LazadaCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        })
        self.base_url = 'https://my.lazada.vn/pdp/review/getReviewList'
    
    def extract_item_id(self, url: str) -> tuple[Optional[int], Optional[int]]:
        """
        Trích xuất itemId và skuId từ URL Lazada
        URL format: https://www.lazada.vn/products/...-i{itemId}-s{skuId}.html
        """
        # Extract itemId
        item_match = re.search(r'-i(\d+)', url)
        item_id = int(item_match.group(1)) if item_match else None
        
        # Extract skuId
        sku_match = re.search(r'-s(\d+)', url)
        sku_id = int(sku_match.group(1)) if sku_match else None
        
        return item_id, sku_id
    
    def get_reviews(self, item_id: int, page: int = 1, page_size: int = 20, 
                    filter_rating: int = 0, sort: int = 0) -> dict:
        """
        Lấy reviews từ API Lazada
        
        Args:
            item_id: ID sản phẩm
            page: Số trang
            page_size: Số reviews mỗi trang (max 50)
            filter_rating: 0=All, 1-5=theo sao
            sort: 0=Relevance, 1=Recent
        """
        params = {
            'itemId': item_id,
            'pageSize': page_size,
            'filter': filter_rating,
            'sort': sort,
            'pageNo': page
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[Lazada] Error fetching reviews: {e}")
            return {}
    
    def get_rating_summary(self, item_id: int) -> dict:
        """Lấy thông tin tổng quan về rating"""
        url = f'https://my.lazada.vn/pdp/review/getRatingSummaryByItemId?itemId={item_id}'
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[Lazada] Error fetching rating summary: {e}")
            return {}
    
    def crawl_all_reviews(self, url: str, max_reviews: int = 5000) -> dict:
        """
        Crawl tất cả reviews từ một sản phẩm Lazada
        
        Args:
            url: URL sản phẩm Lazada
            max_reviews: Số reviews tối đa cần crawl
            
        Returns:
            dict với thông tin sản phẩm và danh sách reviews
        """
        item_id, sku_id = self.extract_item_id(url)
        
        if not item_id:
            return {'error': 'Không thể trích xuất itemId từ URL'}
        
        print(f"[Lazada] Crawling itemId={item_id}, skuId={sku_id}")
        
        # Lấy thông tin tổng quan
        summary = self.get_rating_summary(item_id)
        summary_model = summary.get('model', {})
        total_reviews = summary_model.get('reviewCount', 0)
        rating_average = summary_model.get('average', 0)
        
        print(f"[Lazada] Total reviews: {total_reviews}, Rating: {rating_average}")
        
        all_reviews = []
        seen_ids = set()  # Để tránh duplicate
        page = 1
        page_size = 50  # Max page size
        
        # Crawl với các sort khác nhau để lấy nhiều reviews hơn
        for sort in [0, 1]:  # 0=Relevance, 1=Recent
            page = 1
            empty_count = 0
            
            while len(all_reviews) < max_reviews:
                print(f"[Lazada] Fetching page {page} (sort={sort})...")
                data = self.get_reviews(item_id, page, page_size, filter_rating=0, sort=sort)
                
                if not data.get('success'):
                    print(f"[Lazada] API error at page {page}")
                    break
                
                items = data.get('model', {}).get('items', [])
                if not items:
                    empty_count += 1
                    if empty_count >= 3:
                        print(f"[Lazada] No more reviews (sort={sort})")
                        break
                    continue
                
                empty_count = 0
                added = 0
                for review in items:
                    review_id = review.get('reviewRateId')
                    if review_id and review_id not in seen_ids:
                        seen_ids.add(review_id)
                        added += 1
                        
                        # Parse rating từ reviewRating
                        rating = review.get('rating', 5)
                        
                        all_reviews.append({
                            'review_id': review_id,
                            'rating_star': rating,
                            'comment': review.get('reviewContent', ''),
                            'author_username': review.get('buyerName', ''),
                            'bought_date': review.get('boughtDate', ''),
                            'review_date': review.get('reviewTime', ''),
                            'images': [img.get('url') for img in review.get('images', [])],
                            'video_id': review.get('videoId'),
                            'video_cover': review.get('videoCoverUrl'),
                            'sku_info': review.get('skuInfo', ''),
                            'helpful_count': review.get('likeCount', 0),
                        })
                
                print(f"[Lazada] Page {page}: +{added} new reviews, total: {len(all_reviews)}")
                
                if len(items) < page_size:
                    break
                
                page += 1
                time.sleep(0.3)  # Rate limiting
        
        # Tính phân bố theo sao
        stars_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in all_reviews:
            star = review.get('rating_star', 5)
            if 1 <= star <= 5:
                stars_distribution[star] += 1
        
        result = {
            'platform': 'lazada',
            'item_id': item_id,
            'sku_id': sku_id,
            'url': url,
            'total_reviews': total_reviews,
            'rating_average': rating_average,
            'stars_distribution': stars_distribution,
            'crawled_count': len(all_reviews),
            'crawled_at': datetime.now().isoformat(),
            'reviews': all_reviews
        }
        
        print(f"[Lazada] ✅ Hoàn thành! Đã crawl {len(all_reviews)}/{total_reviews} reviews")
        return result
    
    def save_to_json(self, data: dict, filename: Optional[str] = None):
        """Lưu kết quả vào file JSON"""
        if not filename:
            filename = f"lazada_reviews_{data.get('item_id', 'unknown')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[Lazada] Saved to {filename}")
        return filename


# Test
if __name__ == '__main__':
    crawler = LazadaCrawler()
    
    # Test URL
    url = "https://www.lazada.vn/products/pdp-i2948267068-s14223961486.html"
    
    result = crawler.crawl_all_reviews(url)
    
    if 'error' not in result:
        crawler.save_to_json(result)
        print(f"\nSummary:")
        print(f"  Total: {result['total_reviews']} reviews")
        print(f"  Crawled: {result['crawled_count']} reviews")
        print(f"  Rating: {result['rating_average']}")
        print(f"  Distribution: {result['stars_distribution']}")
    else:
        print(f"Error: {result['error']}")
