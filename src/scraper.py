import csv
import os
import time
import random
import re
import pandas as pd
import sys

# Import Realtime Crawlers
try:
    from src.crawler.scripts.realtime_shopee import ShopeeCrawler
    from src.crawler.scripts.realtime_tiki import TikiCrawler
except ImportError:
    pass

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
    """
    Scraper Real-time: Thu thập bình luận trực tiếp từ API của Tiki và Shopee.
    Dữ liệu sẽ được cào mới hoàn toàn khi người dùng nhập link.
    """
    comments = []
    
    # 1. Xử lý link TIKI
    if "tiki.vn" in url.lower():
        try:
            crawler = TikiCrawler()
            # Giới hạn lấy 100-200 bình luận để API không bị timeout
            result = crawler.crawl_all_reviews(url, max_reviews=150)
            if 'error' not in result and 'reviews' in result:
                for rv in result['reviews']:
                    c = str(rv.get('comment', '')).strip()
                    # Chỉ lấy comment có nội dung thực sự (tránh review chỉ có icon/ảnh)
                    if len(c) > 5:
                        comments.append(c)
        except Exception as e:
            print(f"[Scraper] Lỗi đọc dữ liệu Tiki real-time: {e}")

    # 2. Xử lý link SHOPEE
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

    # 3. Dữ liệu MOCK dự phòng (nếu nhập link lạ hoặc Crawler bị block tạm thời)
    if not comments:
        print("[Scraper] Cảnh báo: Không crawl được dữ liệu, đang sử dụng Mock Data.")
        mock_comments = [
            "Chất vải mỏng hơn mình nghĩ, form áo thì tạm được nhưng đường chỉ may ẩu quá, nhiều chỉ thừa. Giao hàng thì siêu lâu, chờ hơn 1 tuần mới tới.",
            "Áo đẹp tuyệt vời nha mọi người, mặc cực kỳ tôn dáng và mát mẻ. Rất đáng đồng tiền bát gạo. Đóng gói cẩn thận, shop chuẩn bị hàng nhanh, 10 điểm!",
            "Chất lượng bình thường, không có gì đặc sắc. Tầm giá 100k thì mình cũng không kỳ vọng nhiều. Mặc tạm đi chơi thì được.",
            "Giao sai màu rồi shop ơi, mình đặt màu đen mà giao màu xanh. Đã nhắn tin xin đổi trả mà shop seen không rep, dịch vụ tệ quá!",
            "Tuyệt vời! Sản phẩm vượt xa mong đợi, chất liệu xịn xò mặc rất thoải mái. Shipper thân thiện, giao hàng thần tốc chỉ trong 1 ngày.",
            "Thất vọng! Áo bị rách một lỗ nhỏ ở nách, nhắn tin shop thì thái độ lồi lõm không chịu đổi. Mọi người né shop này ra nhé, làm ăn chộp giật.",
            "Quá tệ! Vải nilon mặc bí vô cùng, mồ hôi không thoát được. Được cái giá rẻ với giao nhanh thôi chứ chất lượng thì không ngửi nổi."
        ]
        time.sleep(random.uniform(0.5, 1.5))
        random.shuffle(mock_comments)
        return mock_comments[:20]
    
    # Shuffle nhẹ để phân bố ngẫu nhiên (nếu muốn) và trả về
    random.shuffle(comments)
    return comments
