import time
import random
import os
import re
import pandas as pd

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
                if 'content' in df.columns:
                    # Lấy các bình luận không rỗng
                    real_comments = df['content'].dropna().tolist()
                    if real_comments:
                        # Lấy ngẫu nhiên 5-8 bình luận thật
                        time.sleep(1) # Mô phỏng độ trễ
                        random.shuffle(real_comments)
                        return real_comments[:random.randint(5, 8)]
            except Exception as e:
                print(f"Lỗi đọc file CSV {csv_path}: {e}")

    # 2. Dữ liệu MOCK dự phòng (nếu nhập link lạ)
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
    return mock_comments[:random.randint(5, 8)]
