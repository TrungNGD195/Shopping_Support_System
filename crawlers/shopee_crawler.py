"""
Shopee Product Reviews Crawler (Playwright Version)
Crawl toàn bộ comment, đánh giá sao, ngày tháng comment từ Shopee
Sử dụng Playwright với Edge browser có sẵn trên Windows
"""

from playwright.sync_api import sync_playwright
import pandas as pd
import time
import json
import re
from datetime import datetime
from typing import Optional


class ShopeeCrawler:
    """Crawler để thu thập reviews từ Shopee sử dụng Playwright"""
    
    def __init__(self, headless: bool = True):
        """
        Khởi tạo crawler
        
        Args:
            headless: Chạy browser ẩn (True) hoặc hiển thị (False)
        """
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
    
    def extract_ids_from_url(self, url: str) -> tuple[Optional[int], Optional[int]]:
        """
        Trích xuất shop_id và item_id từ URL Shopee
        
        URL có dạng: https://shopee.vn/product-name-i.{shop_id}.{item_id}
        """
        pattern = r'i\.(\d+)\.(\d+)'
        match = re.search(pattern, url)
        
        if match:
            shop_id = int(match.group(1))
            item_id = int(match.group(2))
            return shop_id, item_id
        
        return None, None

    def crawl_from_url(self, url: str, max_pages: int = 5) -> tuple[dict, list[dict]]:
        """
        Crawl reviews từ URL sản phẩm Shopee
        
        Args:
            url: URL sản phẩm Shopee
            max_pages: Số trang reviews tối đa
            
        Returns:
            Tuple (product_info, reviews)
        """
        shop_id, item_id = self.extract_ids_from_url(url)
        
        if not shop_id or not item_id:
            raise ValueError(f"Không thể trích xuất shop_id và item_id từ URL: {url}")
        
        print(f"Shop ID: {shop_id}, Item ID: {item_id}")
        
        all_reviews = []
        product_info = {"shop_id": shop_id, "item_id": item_id}
        
        with sync_playwright() as p:
            # Sử dụng Edge có sẵn trên Windows
            print("Đang khởi động Edge browser...")
            self.browser = p.chromium.launch(
                headless=self.headless,
                channel="msedge"
            )
            
            context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                locale="vi-VN"
            )
            
            self.page = context.new_page()
            
            try:
                # Truy cập trang sản phẩm
                print("Đang tải trang sản phẩm...")
                self.page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5)
                
                # Lấy thông tin sản phẩm
                product_info = self._get_product_info(shop_id, item_id)
                print(f"Sản phẩm: {product_info.get('name', 'N/A')[:50]}...")
                
                # Scroll xuống phần reviews
                print("Đang scroll đến phần đánh giá...")
                self._scroll_to_reviews()
                
                # Crawl reviews
                for page_num in range(max_pages):
                    print(f"Đang crawl trang {page_num + 1}...")
                    
                    # Lấy reviews từ trang hiện tại
                    reviews = self._extract_reviews_from_page()
                    
                    if not reviews:
                        print("Không còn reviews hoặc không tìm thấy")
                        break
                    
                    all_reviews.extend(reviews)
                    print(f"  Đã lấy {len(reviews)} reviews (Tổng: {len(all_reviews)})")
                    
                    # Chuyển sang trang tiếp theo
                    if not self._go_to_next_page():
                        print("Đã hết trang reviews")
                        break
                    
                    time.sleep(2)
                
            finally:
                self.browser.close()
        
        print(f"Hoàn thành! Tổng số reviews: {len(all_reviews)}")
        return product_info, all_reviews
    
    def _get_product_info(self, shop_id: int, item_id: int) -> dict:
        """Lấy thông tin sản phẩm từ trang"""
        try:
            # Đợi trang load
            self.page.wait_for_selector("section, div[class*='product']", timeout=10000)
            
            # Lấy tên sản phẩm
            name = ""
            try:
                name_elem = self.page.query_selector("h1, div[class*='title'] span, span[class*='title']")
                if name_elem:
                    name = name_elem.inner_text()
            except:
                pass
            
            # Lấy rating
            rating = 0
            try:
                rating_elem = self.page.query_selector("div[class*='rating'] div[class*='score']")
                if rating_elem:
                    rating = float(rating_elem.inner_text())
            except:
                pass
            
            return {
                "name": name[:100] if name else "N/A",
                "shop_id": shop_id,
                "item_id": item_id,
                "rating_star": rating,
            }
        except Exception as e:
            print(f"Lỗi khi lấy thông tin sản phẩm: {e}")
            return {"shop_id": shop_id, "item_id": item_id, "name": "N/A"}
    
    def _scroll_to_reviews(self):
        """Scroll xuống phần reviews"""
        try:
            # Scroll dần xuống để load content
            for i in range(10):
                self.page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                time.sleep(0.5)
            
            # Tìm phần đánh giá sản phẩm
            try:
                review_section = self.page.query_selector("div[class*='product-rating'], div[class*='rating-container']")
                if review_section:
                    review_section.scroll_into_view_if_needed()
                    time.sleep(1)
            except:
                pass
                
        except Exception as e:
            print(f"Lỗi khi scroll: {e}")
    
    def _extract_reviews_from_page(self) -> list[dict]:
        """Trích xuất reviews từ trang hiện tại"""
        reviews = []
        
        try:
            time.sleep(2)
            
            # Tìm các review container với nhiều selector
            selectors = [
                "div.shopee-product-rating",
                "div[class*='product-rating']:not([class*='overview'])",
                "div[class*='rating-comment']",
            ]
            
            review_elements = []
            for selector in selectors:
                elements = self.page.query_selector_all(selector)
                if elements:
                    review_elements = elements
                    break
            
            print(f"  Tìm thấy {len(review_elements)} review containers")
            
            for elem in review_elements:
                review = self._parse_review_element(elem)
                if review and review.get('comment'):
                    reviews.append(review)
            
        except Exception as e:
            print(f"Lỗi khi trích xuất reviews: {e}")
        
        return reviews
    
    def _parse_review_element(self, element) -> Optional[dict]:
        """Parse một review element"""
        try:
            html = element.inner_html()
            
            # Lấy số sao - đếm số icon solid
            rating_star = html.count('icon-rating-solid')
            if rating_star == 0:
                rating_star = 5  # Mặc định
            
            # Lấy nội dung comment
            comment = ""
            try:
                comment_elem = element.query_selector("div[class*='comment'], div[class*='content']")
                if comment_elem:
                    comment = comment_elem.inner_text().strip()
            except:
                pass
            
            # Lấy username
            username = ""
            try:
                user_elem = element.query_selector("a[class*='author'], div[class*='name'], div[class*='author']")
                if user_elem:
                    username = user_elem.inner_text().strip()
            except:
                pass
            
            # Lấy ngày comment
            comment_date = ""
            try:
                date_elem = element.query_selector("div[class*='time'], span[class*='time']")
                if date_elem:
                    comment_date = date_elem.inner_text().strip()
            except:
                pass
            
            # Lấy biến thể sản phẩm
            product_items = ""
            try:
                variant_elem = element.query_selector("div[class*='variation']")
                if variant_elem:
                    product_items = variant_elem.inner_text().replace("Phân loại hàng:", "").strip()
            except:
                pass
            
            # Kiểm tra có hình ảnh/video không
            has_images = 'img' in html.lower() and 'shopee' in html.lower()
            has_video = 'video' in html.lower()
            
            return {
                "rating_star": rating_star,
                "comment": comment,
                "comment_date": comment_date,
                "username": username,
                "product_items": product_items,
                "has_images": has_images,
                "has_video": has_video,
            }
            
        except Exception as e:
            print(f"Lỗi parse review: {e}")
            return None
    
    def _go_to_next_page(self) -> bool:
        """Chuyển sang trang reviews tiếp theo"""
        try:
            # Tìm nút next
            next_btn = self.page.query_selector("button.shopee-icon-button--right:not([disabled])")
            
            if next_btn:
                next_btn.click()
                time.sleep(2)
                return True
            
            # Thử tìm nút tiếp theo khác
            next_buttons = self.page.query_selector_all("button[class*='next'], button svg")
            for btn in next_buttons:
                try:
                    parent = btn.evaluate("el => el.closest('button')")
                    if parent:
                        btn.click()
                        time.sleep(2)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Lỗi khi chuyển trang: {e}")
            return False
    
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
            "product_info": product_info,
            "reviews": reviews,
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_reviews": len(reviews)
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Đã lưu dữ liệu vào {filename}")


# Demo usage
if __name__ == "__main__":
    print("="*50)
    print("SHOPEE REVIEWS CRAWLER")
    print("="*50)
    
    crawler = ShopeeCrawler(headless=False)  # headless=False để xem browser
    
    test_url = input("Nhập URL sản phẩm Shopee: ").strip()
    
    if test_url:
        try:
            product_info, reviews = crawler.crawl_from_url(test_url, max_pages=3)
            
            if reviews:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_file = f"data/raw/shopee_reviews_{timestamp}.csv"
                json_file = f"data/raw/shopee_reviews_{timestamp}.json"
                
                crawler.save_to_csv(reviews, csv_file)
                crawler.save_to_json(product_info, reviews, json_file)
                
                # Hiển thị mẫu
                print("\n--- MẪU REVIEWS ---")
                for i, r in enumerate(reviews[:3]):
                    print(f"\n[{i+1}] {r['rating_star']}⭐ - {r['username']}")
                    comment = r.get('comment', '')
                    print(f"    {comment[:100]}..." if len(comment) > 100 else f"    {comment}")
            else:
                print("Không thu thập được reviews!")
                
        except Exception as e:
            print(f"Lỗi: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Không có URL được nhập!")
