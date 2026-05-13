import pandas as pd
import re
import os
import sys

# Đặt mã hóa UTF-8 cho console để tránh lỗi in chữ tiếng Việt trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# Từ khóa dạng đã được tokenize (nối bằng dấu _)
KEYWORDS = {
    'Quality': {
        'positive': ['tốt', 'tuyệt_vời', 'tuyệt', 'đẹp', 'chắc_chắn', 'xịn', 'ok', 'ổn', 'ưng_ý', 'hài_lòng', 'đúng_mô_tả', 'đúng_hình', 'chất_lượng', 'chính_hãng', 'chuẩn', 'bền', 'thơm', 'mịn', 'đỉnh', 'hay', 'ngon', 'xuất_sắc', 'hoàn_hảo', 'hữu_ích', 'êm', 'mượt', 'nhạy', 'rõ', 'nét', 'sang', 'xịn_xò', 'xịn_sò', 'ưng', 'ưng_bụng', 'đỉnh_của_chóp', 'đáng_mua'],
        'negative': ['tệ', 'xấu', 'hỏng', 'lỗi', 'rởm', 'kém', 'chán', 'dỏm', 'mỏng', 'vỡ', 'móp', 'trầy', 'xước', 'thất_vọng', 'không_giống', 'giả', 'nhái', 'phake', 'không_như', 'yếu', 'dở', 'tồi', 'hôi', 'khét', 'ồn', 'giật', 'lag', 'nóng', 'rách', 'gãy', 'sứt', 'sứt_mẻ', 'đứt', 'rỉ', 'rỉ_sét', 'cũ', 'bẩn', 'dơ']
    },
    'Price': {
        'positive': ['rẻ', 'hợp_lý', 'phải_chăng', 'vừa_tiền', 'đáng_tiền', 'giảm_giá', 'sale', 'rẻ_hơn', 'hời', 'rẻ_bèo', 'giá_tốt', 'giá_ổn', 'giá_mềm', 'giá_sinh_viên'],
        'negative': ['đắt', 'mắc', 'chát', 'không_đáng', 'tốn_tiền', 'phí_tiền', 'cao', 'giá_chát', 'chặt_chém']
    },
    'Delivery': {
        'positive': ['giao_nhanh', 'nhanh', 'cẩn_thận', 'kỹ', 'đóng_gói_tốt', 'hỏa_tốc', 'nhanh_chóng', 'đóng_gói_kỹ', 'shipper_thân_thiện', 'shipper_nhiệt_tình', 'nguyên_vẹn', 'bọc_kỹ', 'chống_sốc', 'giao_đúng_hạn', 'đóng_gói_chắc_chắn', 'giao_sớm'],
        'negative': ['chậm', 'lâu', 'móp_méo', 'rách', 'vỡ_hộp', 'giao_lâu', 'chờ_dài_cổ', 'hư_hỏng_trong_lúc_giao', 'gãy', 'giao_trễ', 'móp', 'nát', 'bể', 'thất_lạc', 'giao_thiếu', 'thiếu_hàng']
    },
    'Service': {
        'positive': ['nhiệt_tình', 'chu_đáo', 'dễ_thương', 'tư_vấn', 'hỗ_trợ', 'phản_hồi_nhanh', 'uy_tín', 'shop_tốt', 'có_tâm', 'bảo_hành_tốt', 'thân_thiện', 'rep_inbox_nhanh'],
        'negative': ['thái_độ', 'vô_trách_nhiệm', 'lừa_đảo', 'không_trả_lời', 'thờ_ơ', 'treo_đầu_dê', 'chửi', 'bom_hàng', 'thiếu_trách_nhiệm', 'tệ_bạc', 'chảnh', 'lơ_khách', 'không_hỗ_trợ', 'block_khách']
    }
}

# Negative prefix to flip sentiment if they appear right before a positive keyword
NEGATIONS = ['không', 'chả', 'chưa', 'đếch', 'kém', 'ko', 'k']

def assign_label(text, aspect):
    if not isinstance(text, str):
        return -1
    
    text = text.lower()
    words = text.split()
    
    pos_score = 0
    neg_score = 0
    
    pos_keywords = KEYWORDS[aspect]['positive']
    neg_keywords = KEYWORDS[aspect]['negative']
    
    for i, word in enumerate(words):
        # Tăng khoảng cách cửa sổ bắt từ phủ định lên 5 từ
        has_negation = False
        start_idx = max(0, i - 5)
        if any(w in NEGATIONS for w in words[start_idx:i]):
            has_negation = True
            
        # Loại trừ chữ "hay" khi nó đóng vai trò là "hoặc" (thường đứng giữa 2 tính từ xấu)
        if word == 'hay' and (i > 0 and i < len(words)-1):
            if any(bad in words[i-1] for bad in neg_keywords) or any(bad in words[i+1] for bad in neg_keywords):
                continue

        if any(kw == word for kw in neg_keywords):
            if has_negation:
                pos_score += 1
            else:
                neg_score += 1
                
        if any(kw == word for kw in pos_keywords):
            if has_negation:
                neg_score += 1
            else:
                pos_score += 1

    if pos_score > 0 and neg_score == 0:
        return 2  # Tích cực
    elif neg_score > 0 and pos_score == 0:
        return 0  # Tiêu cực
    elif pos_score > 0 and neg_score > 0:
        # Xử lý Tie (Hòa): Nếu khen chê bằng nhau, ưu tiên Khen (vì đa số là review 5 sao)
        return 2 if pos_score >= neg_score else 0
    elif pos_score == 0 and neg_score == 0:
        # Nếu có từ khóa liên quan đến aspect nhưng không rõ khen chê (trung tính)
        aspect_indicators = {
            'Quality': ['chất_lượng', 'sản_phẩm', 'hàng', 'màu', 'size'],
            'Price': ['giá', 'tiền', 'giá_cả', 'giá_thành'],
            'Delivery': ['giao', 'ship', 'đóng_gói', 'vận_chuyển', 'nhận_hàng'],
            'Service': ['shop', 'chủ_shop', 'nhân_viên', 'tư_vấn', 'trả_lời']
        }
        if any(ind in text for ind in aspect_indicators[aspect]):
            return 1 # Bình thường / Trung tính
        return -1 # Không nhắc tới

def main():
    data_dir = r"d:\Shopping_Support_System\data"
    files = ["auto_labeled_cleaned_negative_reviews.csv", "auto_labeled_cleaned_positive_reviews.csv"]
    
    for file in files:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            print(f"Đang gán nhãn tự động cho file: {file}...")
            df = pd.read_csv(file_path)
            
            # Gán nhãn cho 4 khía cạnh
            for aspect in ['Quality', 'Price', 'Delivery', 'Service']:
                df[aspect] = df['cleaned_comment'].apply(lambda x: assign_label(x, aspect))
            
            # Lưu đè ra file cũ (bỏ tiền tố auto_labeled_ bị lặp)
            output_file = os.path.join(data_dir, file)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            # Thống kê nhanh
            print(f"Đã lưu: {output_file}")
            print("Thống kê nhãn (2: Khen, 1: Bình thường, 0: Chê, -1: Không nhắc):")
            for aspect in ['Quality', 'Price', 'Delivery', 'Service']:
                counts = df[aspect].value_counts().to_dict()
                print(f"  - {aspect}: {counts}")
            print("-" * 40)
        else:
            print(f"Không tìm thấy file: {file_path}")

if __name__ == "__main__":
    main()
