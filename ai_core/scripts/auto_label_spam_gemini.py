import pandas as pd

def is_spam_heuristic(text):
    text = str(text).lower()
    
    # Những từ khóa báo hiệu đánh giá thật (Bổ sung thêm hàng loạt từ vựng mua sắm chung)
    real_keywords = [
        "vải", "chất", "đẹp", "xấu", "rẻ", "đắt", "màu", "size", "form", "mặc", 
        "giao", "shop", "gói", "tư", "vấn", "thơm", "xịn", "ok", "tốt", "ưng", "nhanh", "chậm",
        "nồi", "máy", "thiết", "kế", "dùng", "sử", "dụng", "mua", "test", "hàng", "tiền", "giá",
        "bảo hành", "chắc", "bền", "lỗi", "hư", "hỏng", "thích", "tuyệt", "kém", "tệ",
        "áo", "quần", "ủi", "nước", "nhựa", "kim loại", "tạm", "ổn", "khen", "chê",
        "thất vọng", "hài lòng", "đáng", "phí", "xứng", "chất lượng", "vừa", "rộng", "chật",
        "ngắn", "dài", "mỏng", "dày", "cứng", "mềm", "mịn", "xù", "nóng", "mát",
        "chạy", "êm", "ồn", "giặt", "sạch", "pin", "sạc", "màn", "âm thanh", "chuẩn",
        "đóng gói", "cẩn thận", "nhẹ", "nặng", "to", "nhỏ", "bóp", "kéo", "khóa", "túi"
    ]
                     
    real_count = sum(1 for kw in real_keywords if kw in text)
    
    # 1. Chặn Thơ ca / Lời bài hát (Spam dài)
    if text.count('\n') >= 3 and len(text) > 80:
        if real_count < 2:
            return 0
            
    # 2. Chặn Spam nhận xu / văn mẫu
    if any(kw in text for kw in ["nhận xu", "lấy xu", "săn xu", "mang tính chất", "chống trôi"]):
        # Chỉ cần có 2 từ khóa mô tả sản phẩm HOẶC câu dài hơn 50 ký tự có chứa 1 từ khóa (như đánh giá bàn ủi)
        if real_count >= 2 or (len(text) > 50 and real_count >= 1):
            pass 
        else:
            return 0 
            
    # 3. Quá ngắn và hoàn toàn vô nghĩa
    if len(text.strip()) < 5:
        return 0
        
    return 1

def auto_label_spam():
    print("[1] Đang quét TOÀN BỘ 26,000+ bình luận trong kho dữ liệu...")
    try:
        df_pos = pd.read_csv("data/positive_reviews.csv")
        df_neg = pd.read_csv("data/negative_reviews.csv")
    except:
        print("Lỗi: Không tìm thấy file data. Đảm bảo chạy đúng thư mục.")
        return
        
    df_train = pd.concat([df_pos, df_neg])['comment'].dropna().tolist()
    
    labeled_data = []
    print(f"[2] Đang gán nhãn cho {len(df_train)} bình luận...")
    
    for i, cmt in enumerate(df_train):
        label = is_spam_heuristic(cmt)
        labeled_data.append({"comment": cmt, "is_spam": label})
        if (i+1) % 5000 == 0:
            print(f"[{i+1}/{len(df_train)}] Đã xử lý...")
            
    df_result = pd.DataFrame(labeled_data)
    df_result.to_csv("data/spam_dataset.csv", index=False)
    
    total_spam = len(df_result[df_result['is_spam'] == 0])
    total_real = len(df_result[df_result['is_spam'] == 1])
    
    print(f"\n[3] HOÀN TẤT! Đã gán nhãn xong: {total_real} Review thật, {total_spam} Spam/Thơ ca.")
    print("Dữ liệu được lưu tại data/spam_dataset.csv")

if __name__ == "__main__":
    auto_label_spam()
