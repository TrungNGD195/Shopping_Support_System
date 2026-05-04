import pandas as pd
import random
import os
import sys

# Import 2 module đã viết ở Bước 1 và Bước 3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from inference import ABSAPredictor
from summarizer import ReviewSummarizer

def run_full_pipeline():
    print("="*60)
    print("   BẮT ĐẦU CHẠY THỰC TẾ LUỒNG XỬ LÝ AI ĐẦY ĐỦ (PIPELINE)")
    print("="*60)
    
    # 1. ĐỌC DỮ LIỆU THỰC TẾ (CRAWL ĐƯỢC TỪ SHOPEE)
    print("\n[Bước 1] Đang nạp dữ liệu từ thư mục 'data'...")
    try:
        df_pos = pd.read_csv(r"d:\Shopping_Support_System\data\positive_reviews.csv")
        df_neg = pd.read_csv(r"d:\Shopping_Support_System\data\negative_reviews.csv")
        
        # Trộn ngẫu nhiên 50 lời khen và 50 lời chê để tạo thành 100 bình luận
        sample_comments = df_pos['comment'].dropna().sample(30).tolist() + df_neg['comment'].dropna().sample(30).tolist()
        random.shuffle(sample_comments)
        print(f"=> Đã bốc ngẫu nhiên {len(sample_comments)} bình luận thực tế của 1 sản phẩm.")
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return

    # 2. GỌI PHOBERT CHẤM ĐIỂM (PHÂN LOẠI SẮC THÁI)
    print("\n[Bước 2] Đang đánh thức PhoBERT để chấm điểm 60 bình luận này...")
    model_dir = r"d:\Shopping_Support_System\models\phobert-absa-final"
    predictor = ABSAPredictor(model_dir)
    
    # Tạo 4 cái rổ (Dictionary) để chứa Khen/Chê cho 4 khía cạnh
    aspects = ['Quality', 'Price', 'Delivery', 'Service']
    khen_dict = {asp: [] for asp in aspects}
    che_dict = {asp: [] for asp in aspects}
    
    print("Đang quét từng bình luận (Mất khoảng 10-20 giây)...")
    for i, c in enumerate(sample_comments):
        # In tiến độ ra màn hình
        if i % 10 == 0 and i > 0:
            print(f"... đã quét {i}/{len(sample_comments)} bình luận")
            
        preds = predictor.predict(c)
        # Phân loại cho cả 4 khía cạnh
        for asp in aspects:
            if preds[asp] == "Tích cực (Khen)":
                khen_dict[asp].append(c)
            elif preds[asp] == "Tiêu cực (Chê)":
                che_dict[asp].append(c)
                
    print("\n[Bước 3] Ném từng rổ Khía cạnh cho Gemini để viết tóm tắt...")
    API_KEY = "AIzaSyAHtaMW99Y9qMTLtsqEgvLZNY47Y28GXio"
    summarizer = ReviewSummarizer(api_key=API_KEY)
    
    print("\n" + "="*80)
    print("KẾT QUẢ CUỐI CÙNG HIỂN THỊ TRÊN GIAO DIỆN WEB (PHÂN TÍCH ĐA KHÍA CẠNH):")
    print("="*80)
    
    # Dịch tên khía cạnh sang tiếng Việt để in ra cho đẹp
    vi_aspects = {'Quality': 'Chất lượng', 'Price': 'Giá cả', 'Delivery': 'Giao hàng', 'Service': 'Dịch vụ CSKH'}
    
    for asp in aspects:
        print(f"\n--- [ Khía cạnh: {vi_aspects[asp].upper()} ] ---")
        print(f"(Có {len(khen_dict[asp])} người khen, {len(che_dict[asp])} người chê)")
        
        if not khen_dict[asp] and not che_dict[asp]:
            print("=> Không có ai bàn luận về khía cạnh này.")
        else:
            summary_text = summarizer.summarize(vi_aspects[asp], khen_dict[asp], che_dict[asp])
            print("=>", summary_text)
            
    print("\n" + "="*80)

if __name__ == "__main__":
    run_full_pipeline()
