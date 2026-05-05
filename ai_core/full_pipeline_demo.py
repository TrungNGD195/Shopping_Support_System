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
    print("   BAT DAU CHAY PIPELINE AI DAY DU")
    print("=" * 60)

    # 1. READ DATA
    print("\n[Buoc 1] Nap du lieu tu thu muc 'data'...")
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
        print(f"=> Da lay ngau nhien {len(sample_comments)} binh luan thuc te.")
    except Exception as e:
        print(f"Loi doc file: {e}")
        return

    # 2. LOAD MODEL & PREDICT
    print("\n[Buoc 2] Khoi dong PhoBERT de cham diem...")

    model_dir = os.path.join(PROJECT_ROOT, "models")
    model_dirs = {
        "Quality": os.path.join(model_dir, "quality_model"),
        "Price": os.path.join(model_dir, "price_model"),
        "Delivery": os.path.join(model_dir, "delivery_model"),
        "Service": os.path.join(model_dir, "service_model"),
    }

    has_models = all(os.path.isdir(p) for p in model_dirs.values())

    if not has_models:
        print("[CANH BAO] Khong tim thay mo hinh trong thu muc 'models/'.")
        print("  Can 4 thu muc: quality_model, price_model, delivery_model, service_model")
        print("  Hay train mo hinh tren Colab bang notebook colab_train_absa.ipynb")
        print("  Sau do tai trained_models.zip ve va giai nen vao thu muc 'models/'.")
        print("\n  [DEMO] Dung du lieu co dinh de minh hoa pipeline...\n")

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
                    label = -1  # Khong nhac toi
                result["aspects"][asp] = {"label": label, "text": str(label)}
            demo_results.append(result)
    else:
        # Use real src/inference.py ABSAPredictor
        predictor = ABSAPredictor()
        demo_results = []
        print("Dang quet tung binh luan...")
        for i, c in enumerate(sample_comments):
            if i % 10 == 0 and i > 0:
                print(f"... da quet {i}/{len(sample_comments)}")
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
    print("\n[Buoc 3] Goi Gemini de viet tom tat...")
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("[CANH BAO] Chua dat bien moi truong GEMINI_API_KEY. Bo qua buoc tom tat.")
        has_summarizer = False
        API_KEY = None

    if API_KEY:
        try:
            summarizer = ReviewSummarizer(api_key=API_KEY)
            has_summarizer = True
        except Exception as e:
            print(f"[CANH BAO] Khong khoi dong duoc Gemini: {e}")
            has_summarizer = False
    else:
        has_summarizer = False

    # 5. DISPLAY RESULTS
    print("\n" + "=" * 80)
    print("KET QUA PHAN TICH DA KHIA CANH:")
    print("=" * 80)

    vi_aspects = {'Quality': 'Chat luong', 'Price': 'Gia ca', 'Delivery': 'Giao hang', 'Service': 'Dich vu CSKH'}
    total_khen = 0
    total_che = 0

    for asp in aspects:
        n_khen = len(khen_dict[asp])
        n_che = len(che_dict[asp])
        total_khen += n_khen
        total_che += n_che

        print(f"\n--- [ {vi_aspects[asp].upper()} ] ---")
        print(f"  Khen: {n_khen} | Che: {n_che}")

        if has_summarizer and (khen_dict[asp] or che_dict[asp]):
            summary = summarizer.summarize(vi_aspects[asp], khen_dict[asp][:10], che_dict[asp][:10])
            print(f"  Tom tat: {summary}")
        elif khen_dict[asp] or che_dict[asp]:
            if khen_dict[asp]:
                print(f"  Khen: {khen_dict[asp][0][:80]}...")
            if che_dict[asp]:
                print(f"  Che:  {che_dict[asp][0][:80]}...")
        else:
            print("  Khong co ai ban luan ve khia canh nay.")

    print("\n" + "=" * 80)
    print("TONG HOP:")
    if total_khen > total_che:
        verdict = "RAT DANG MUA"
    elif total_che > total_khen:
        verdict = "CAN CAN NHAC"
    else:
        verdict = "PHAN VAN (TRUNG LAP)"
    print(f"  Tong khen: {total_khen} | Tong che: {total_che}")
    print(f"  Khuyen nghi: {verdict}")
    print("=" * 80)


if __name__ == "__main__":
    run_full_pipeline()
