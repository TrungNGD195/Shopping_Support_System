import csv
import os
import re
import random
import os
import re
import pandas as pd

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
    """
    Scraper tích hợp: Lấy dữ liệu bình luận thật từ file CSV dựa vào Product ID trên URL.
    Nếu không tìm thấy hoặc URL không hợp lệ, trả về dữ liệu Mock.
    """
    # 1. Tìm Product ID trong URL (VD: tiki.vn/product-p24951095.html -> 24951095)
    match = re.search(r'-p(\d+)\.html', url)
    if match:
        product_id = match.group(1)
        csv_path = os.path.join("archive_raw_data", f"tiki_{product_id}.csv")
        
        # Nếu có file CSV thật từ quá trình crawl trước đó
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if 'comment' in df.columns:
                    # Lấy các bình luận không rỗng
                    real_comments = df['comment'].dropna().tolist()
                    if real_comments:
                        # Ưu tiên lấy 50 bình luận DÀI NHẤT và CHI TIẾT NHẤT
                        real_comments.sort(key=lambda x: len(str(x)), reverse=True)
                        time.sleep(1) # Mô phỏng độ trễ
                        return real_comments[:50]
            except Exception as e:
                print(f"Lỗi đọc file CSV {csv_path}: {e}")

    # 2. Xử lý link Shopee (Lấy chính xác bình luận của sản phẩm nếu có)
    if "shopee.vn" in url.lower():
        # Lấy Product ID từ link Shopee (VD: i.12345.28506866571 -> 28506866571)
        match_shopee = re.search(r'-i\.\d+\.(\d+)', url) or re.search(r'/product/\d+/(\d+)', url)
        shopee_id = match_shopee.group(1) if match_shopee else None

        # 2a. ƯU TIÊN 1: Đọc từ file Excel chứa Demo Data (nếu có)
        try:
            excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Shopee_Reviews_3h34 (1).xlsx")
            if os.path.exists(excel_path) and shopee_id:
                df_excel = pd.read_excel(excel_path)
                # Lọc các dòng có Link Sản Phẩm chứa shopee_id
                matched_df = df_excel[df_excel['Link Sản Phẩm'].str.contains(shopee_id, na=False)]
                if not matched_df.empty:
                    excel_comments = matched_df['Nội dung'].dropna().tolist()
                    if excel_comments:
                        time.sleep(1)
                        # Trả về các bình luận từ file Excel
                        return excel_comments[:50]
        except Exception as e:
            print(f"Lỗi đọc file Excel Demo: {e}")

        # 2b. ƯU TIÊN 2: Đọc từ file CSV (chỉ lấy đúng ID, KHÔNG lấy random)
        try:
            pos_path = os.path.join("data", "positive_reviews.csv")
            neg_path = os.path.join("data", "negative_reviews.csv")
            shopee_comments = []
            
            # Hàm đọc và lọc comment, ưu tiên DÀI NHẤT
            def get_longest_shopee_comments(path, prod_id, limit=25):
                if not os.path.exists(path) or not prod_id: return []
                df = pd.read_csv(path, dtype={'product_id': str})
                
                exact_df = df[df['product_id'] == prod_id]
                if not exact_df.empty:
                    comments = exact_df['comment'].dropna().tolist()
                    comments.sort(key=lambda x: len(str(x)), reverse=True)
                    return comments[:limit]
                return []
            
            # Lấy 25 câu khen dài nhất + 25 câu chê dài nhất = 50 câu cân bằng
            shopee_comments.extend(get_longest_shopee_comments(pos_path, shopee_id, 25))
            shopee_comments.extend(get_longest_shopee_comments(neg_path, shopee_id, 25))
                
            if shopee_comments:
                time.sleep(1)
                random.shuffle(shopee_comments) # Xáo trộn khen/chê để không bị cụm
                return shopee_comments
        except Exception as e:
            print(f"Lỗi đọc dữ liệu Shopee: {e}")

    # 3. Dữ liệu MOCK dự phòng (nếu nhập link lạ)
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
