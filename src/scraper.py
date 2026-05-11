import time
import random

def get_reviews_from_url(url: str) -> list[str]:
    """
    Mock scraper: Lấy dữ liệu bình luận từ URL (Mô phỏng).
    Trong thực tế, bạn sẽ gọi crawl_reviews.py hoặc API bên thứ 3 ở đây.
    """
    # Trả về các bình luận siêu thực tế để trình diễn AI
    mock_comments = [
        "Chất vải mỏng hơn mình nghĩ, form áo thì tạm được nhưng đường chỉ may ẩu quá, nhiều chỉ thừa. Giao hàng thì siêu lâu, chờ hơn 1 tuần mới tới.",
        "Áo đẹp tuyệt vời nha mọi người, mặc cực kỳ tôn dáng và mát mẻ. Rất đáng đồng tiền bát gạo. Đóng gói cẩn thận, shop chuẩn bị hàng nhanh, 10 điểm!",
        "Chất lượng bình thường, không có gì đặc sắc. Tầm giá 100k thì mình cũng không kỳ vọng nhiều. Mặc tạm đi chơi thì được.",
        "Giao sai màu rồi shop ơi, mình đặt màu đen mà giao màu xanh. Đã nhắn tin xin đổi trả mà shop seen không rep, dịch vụ tệ quá!",
        "Hàng xịn xò lắm, form y hình. Vải co giãn thoải mái. Tuy nhiên hộp bị móp méo chút xíu do vận chuyển, bên trong vẫn nguyên vẹn.",
        "Tuyệt vời! Sản phẩm vượt xa mong đợi, chất liệu xịn xò mặc rất thoải mái. Shipper thân thiện, giao hàng thần tốc chỉ trong 1 ngày.",
        "Thất vọng! Áo bị rách một lỗ nhỏ ở nách, nhắn tin shop thì thái độ lồi lõm không chịu đổi. Mọi người né shop này ra nhé, làm ăn chộp giật.",
        "Cũng tạm ổn, màu nhạt hơn trong hình một chút. Ship nhanh, đóng gói chắc chắn. Với giá này thì mua mặc ở nhà cũng oke.",
        "Shop phục vụ siêu tốt, mình lỡ đặt nhầm size nhắn tin đổi shop hỗ trợ rất nhiệt tình. Áo chất len tăm dày dặn, mặc thích lắm.",
        "Quá tệ! Vải nilon mặc bí vô cùng, mồ hôi không thoát được. Được cái giá rẻ với giao nhanh thôi chứ chất lượng thì không ngửi nổi."
    ]
    
    # Mô phỏng độ trễ của mạng khi cào dữ liệu thật (0.5s - 1.5s)
    time.sleep(random.uniform(0.5, 1.5))
    
    # Trộn ngẫu nhiên và lấy ra 5-8 bình luận để mỗi lần phân tích có sự khác biệt
    random.shuffle(mock_comments)
    return mock_comments[:random.randint(5, 8)]
