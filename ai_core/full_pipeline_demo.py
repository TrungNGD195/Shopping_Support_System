import pandas as pd
import random
import os
import sys
import io
from dotenv import load_dotenv

# Project root (2 levels up from this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env from ai_core/ directory
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inference import ABSAPredictor
from summarizer import ReviewSummarizer

def run_full_pipeline():
    print("=" * 60)
    print("   BẮT ĐẦU CHẠY PIPELINE AI ĐẦY ĐỦ")
    print("=" * 60)

    # 1. READ DATA
    print("\n[Bước 1] Nạp dữ liệu từ thư mục 'data'...")
    try:
        def read_csv_safe(path):
            with open(path, 'rb') as f:
                return pd.read_csv(io.StringIO(f.read().decode('cp1258', errors='replace')))

        df_pos = read_csv_safe(os.path.join(PROJECT_ROOT, "data", "auto_labeled_cleaned_positive_reviews.csv"))
        df_neg = read_csv_safe(os.path.join(PROJECT_ROOT, "data", "auto_labeled_cleaned_negative_reviews.csv"))

        n_pos = min(30, len(df_pos))
        n_neg = min(30, len(df_neg))
        sample_comments = df_pos['comment'].dropna().sample(n_pos).tolist() + df_neg['comment'].dropna().sample(n_neg).tolist()
        random.shuffle(sample_comments)
        print(f"=> Đã lấy ngẫu nhiên {len(sample_comments)} bình luận thực tế.")
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return

    # 2. LOAD MODEL & PREDICT
    print("\n[Bước 2] Khởi động PhoBERT để chấm điểm...")

    model_dir = os.path.join(PROJECT_ROOT, "models")
    model_dirs = {
        "Quality": os.path.join(model_dir, "quality_model"),
        "Price": os.path.join(model_dir, "price_model"),
        "Delivery": os.path.join(model_dir, "delivery_model"),
        "Service": os.path.join(model_dir, "service_model"),
    }

    has_models = all(os.path.isdir(p) for p in model_dirs.values())

    if not has_models:
        print("[CẢNH BÁO] Không tìm thấy mô hình trong thư mục 'models/'.")
        print("  Cần 4 thư mục: quality_model, price_model, delivery_model, service_model")
        print("  Hãy train mô hình trên Colab bằng notebook colab_train_absa.ipynb")
        print("  Sau đó tải trained_models.zip về và giải nén vào thư mục 'models/'.")
        print("\n  [DEMO] Dùng dữ liệu cố định để minh họa pipeline...\n")

        # Hardcoded demo data (simulates model output)
        demo_results = []
        for c in sample_comments:
            result = {"original_text": c, "aspects": {}}
            lower = c.lower()
            for asp in ["Quality", "Price", "Delivery", "Service"]:
                if asp == "Quality" and any(w in lower for w in ["đẹp", "tốt", "xịn", "chất", "mượt", "đẹp", "xấu", "hỏng", "kém", "nhái"]):
                    label = 2 if any(w in lower for w in ["đẹp", "tốt", "xịn", "chất", "mượt"]) else 0
                elif asp == "Price" and any(w in lower for w in ["giá", "đắt", "rẻ", "sale", "tiền", "worth"]):
                    label = 2 if any(w in lower for w in ["rẻ", "sale", "worth"]) else 0
                elif asp == "Delivery" and any(w in lower for w in ["giao", "ship", "nhanh", "chậm", "đóng gói"]):
                    label = 2 if any(w in lower for w in ["nhanh", "hỏa tốc"]) else 0
                elif asp == "Service" and any(w in lower for w in ["shop", "tư vấn", "trả lời", "nhiệt tình", "rep", "hỗ trợ"]):
                    label = 2 if any(w in lower for w in ["nhiệt tình", "tư vấn"]) else 0
                else:
                    label = -1  # Không nhắc tới
                result["aspects"][asp] = {"label": label, "text": str(label)}
            demo_results.append(result)
    else:
        # Use real src/inference.py ABSAPredictor
        predictor = ABSAPredictor()
        demo_results = []
        print("Đang quét từng bình luận...")
        for i, c in enumerate(sample_comments):
            if i % 10 == 0 and i > 0:
                print(f"... đã quét {i}/{len(sample_comments)}")
            demo_results.append(predictor.predict_single_comment(c))

    # 3. AGGREGATE
    aspects = ['Quality', 'Price', 'Delivery', 'Service']
    khen_dict = {asp: [] for asp in aspects}
    che_dict = {asp: [] for asp in aspects}

    for result in demo_results:
        for asp in aspects:
            label = result["aspects"].get(asp, {}).get("label", -1)
            if label == 2:
                khen_dict[asp].append(result["original_text"])
            elif label == 0:
                che_dict[asp].append(result["original_text"])

    # 4. SUMMARIZE WITH GEMINI
    print("\n[Bước 3] Gọi Gemini để viết tóm tắt...")
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("[CẢNH BÁO] Chưa đặt biến môi trường GEMINI_API_KEY. Bỏ qua bước tóm tắt.")
        has_summarizer = False
        API_KEY = None

    if API_KEY:
        try:
            summarizer = ReviewSummarizer(api_key=API_KEY)
            has_summarizer = True
        except Exception as e:
            print(f"[CẢNH BÁO] Không khởi động được Gemini: {e}")
            has_summarizer = False
    else:
        has_summarizer = False

    # 5. DISPLAY RESULTS
    print("\n" + "=" * 80)
    print("KẾT QUẢ PHÂN TÍCH ĐA KHÍA CẠNH:")
    print("=" * 80)

    vi_aspects = {'Quality': 'Chất lượng', 'Price': 'Giá cả', 'Delivery': 'Giao hàng', 'Service': 'Dịch vụ CSKH'}
    total_khen = 0
    total_che = 0

    for asp in aspects:
        n_khen = len(khen_dict[asp])
        n_che = len(che_dict[asp])
        total_khen += n_khen
        total_che += n_che

        print(f"\n--- [ {vi_aspects[asp].upper()} ] ---")
        print(f"  Khen: {n_khen} | Chê: {n_che}")

        if has_summarizer and (khen_dict[asp] or che_dict[asp]):
            summary = summarizer.summarize(vi_aspects[asp], khen_dict[asp][:10], che_dict[asp][:10])
            print(f"  Tóm tắt: {summary}")
        elif khen_dict[asp] or che_dict[asp]:
            if khen_dict[asp]:
                print(f"  Khen: {khen_dict[asp][0][:80]}...")
            if che_dict[asp]:
                print(f"  Chê:  {che_dict[asp][0][:80]}...")
        else:
            print("  Không có ai bàn luận về khía cạnh này.")

    print("\n" + "=" * 80)
    print("TỔNG HỢP:")
    if total_khen > total_che:
        verdict = "RẤT ĐÁNG MUA"
    elif total_che > total_khen:
        verdict = "CẦN CÂN NHẮC"
    else:
        verdict = "PHÂN VÂN (TRUNG LẬP)"
    print(f"  Tổng khen: {total_khen} | Tổng chê: {total_che}")
    print(f"  Khuyến nghị: {verdict}")
    print("=" * 80)


if __name__ == "__main__":
    run_full_pipeline()
