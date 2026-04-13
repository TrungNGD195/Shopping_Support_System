"""
Base Crawler Class
Lớp cơ sở cho các crawler khác kế thừa
"""

from abc import ABC, abstractmethod
import pandas as pd
import json
from datetime import datetime
from typing import Optional


class BaseCrawler(ABC):
    """Abstract base class cho các crawler"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    @abstractmethod
    def extract_ids_from_url(self, url: str) -> tuple:
        """Trích xuất ID từ URL sản phẩm"""
        pass
    
    @abstractmethod
    def crawl_reviews(self, **kwargs) -> list[dict]:
        """Crawl reviews từ sản phẩm"""
        pass
    
    @abstractmethod
    def crawl_from_url(self, url: str, **kwargs) -> tuple[dict, list[dict]]:
        """Crawl từ URL sản phẩm - trả về (product_info, reviews)"""
        pass
    
    def save_to_csv(self, reviews: list[dict], filename: str):
        """Lưu reviews ra file CSV"""
        if not reviews:
            print("Không có reviews để lưu")
            return
        
        df = pd.DataFrame(reviews)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"Đã lưu {len(reviews)} reviews vào {filename}")
    
    def save_to_json(self, product_info: dict, reviews: list[dict], filename: str):
        """Lưu thông tin sản phẩm và reviews ra file JSON"""
        data = {
            "platform": self.platform_name,
            "product_info": product_info,
            "reviews": reviews,
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_reviews": len(reviews)
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Đã lưu dữ liệu vào {filename}")
    
    def get_statistics(self, reviews: list[dict]) -> dict:
        """Tính thống kê cơ bản từ reviews"""
        if not reviews:
            return {}
        
        df = pd.DataFrame(reviews)
        
        stats = {
            "total_reviews": len(df),
            "rating_distribution": df['rating_star'].value_counts().to_dict() if 'rating_star' in df.columns else {},
            "avg_rating": df['rating_star'].mean() if 'rating_star' in df.columns else 0,
            "reviews_with_comment": len(df[df['comment'] != '']) if 'comment' in df.columns else 0,
        }
        
        if 'has_images' in df.columns:
            stats["reviews_with_images"] = df['has_images'].sum()
        
        if 'has_video' in df.columns:
            stats["reviews_with_video"] = df['has_video'].sum()
        
        return stats
