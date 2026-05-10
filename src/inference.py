import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import time
import sys
import os

# Đảm bảo import utils từ thư mục src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import hàm clean_text đầy đủ (teencode, word_tokenize, etc.)
try:
    from utils.text_processing import clean_text
except ImportError:
    # Hàm dự phòng nếu chưa nối file utils
    def clean_text(text): return text.lower().strip()

def safe_print(text):
    try:
        # Ép kiểu encode bỏ qua các ký tự không được hỗ trợ trên Windows Console
        print(str(text).encode('ascii', 'ignore').decode('ascii'))
    except Exception:
        pass

class ABSAPredictor:
    """
    Class này đóng vai trò là Trạm Trí Tuệ.
    Nạp 1 mô hình PhoBERT ABSA vào RAM, chạy 4 khía cạnh qua cùng 1 model.
    """
    def __init__(self):
        # 1. Xác định thiết bị
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        safe_print(f"[INFO] Dang khoi dong AI tren thiet bi: {self.device}")

        # 2. 4 khía cạnh cần đánh giá (aspect text gửi kèm comment cho model)
        self.aspects = {
            'Quality': 'chất lượng',
            'Price': 'giá cả',
            'Delivery': 'giao hàng',
            'Service': 'dịch vụ'
        }

        # 3. Thử load mô hình ABSA từ models/phobert-absa-final
        self.model = None
        self.tokenizer = None
        self.mock_mode = False

        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "phobert-absa-final")
        if os.path.isdir(model_path):
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_path, use_safetensors=True)
                self.model.to(self.device)
                self.model.eval()
                safe_print(f"[SUCCESS] Da nap mo hinh ABSA tu: {model_path}")
            except Exception as e:
                safe_print(f"[WARNING] Loi load mo hinh tu {model_path}: {e}")
                self.model = None
        else:
            safe_print(f"[WARNING] Khong tim thay mo hinh tai {model_path}")

        # 4. Fallback: keyword-based mock
        if not self.model:
            self.mock_mode = True
            safe_print("[INFO] Chuyen sang che do MOCK (keyword-based).")

        # 5. Label map cho mô hình ABSA (theo Kaggle training: 0=Chê, 1=BT, 2=Khen, 3=Không nhắc tới)
        self.label_map = {
            0: {"label": 0,  "text": "🔴 Chê"},
            1: {"label": 1,  "text": "🟡 Bình thường"},
            2: {"label": 2,  "text": "🟢 Khen"},
            3: {"label": -1, "text": "⚪ Không nhắc tới"}
        }

    def _mock_predict(self, comment):
        """Dự đoán mô phỏng bằng keyword matching khi chưa có model thật."""
        lower = comment.lower()
        result = {"original_text": comment, "aspects": {}}

        # Detect concessive/overall-negative patterns:
        # "Được cái X thôi chứ Y", "Tuy X nhưng Y", "Mặc dù X nhưng Y", "X nhưng mà Y"
        # These mean the overall sentiment is negative despite mentioning positives.
        concessive_patterns = [
            "thôi chứ", "chứ chất lượng", "chứ không",
            "tuy ", "tuyệt vời nhưng", "mặc dù",
            "nhưng mà", "được cái", "được mỗi",
        ]
        strong_negative = [
            "quá tệ", "tệ quá", "rác", "lừa đảo", "scam", "đồ đểu",
            "hàng fake", "hàng nhái", "thất vọng", "không ngửi nổi",
            "chộp giật", "né shop", "không bao giờ mua",
        ]

        has_concessive = any(p in lower for p in concessive_patterns)
        has_strong_neg = any(p in lower for p in strong_negative)

        # If comment has concessive pattern + strong negative → overall negative
        # Suppress positive labels on all aspects in that case
        overall_negative = has_concessive and has_strong_neg

        keyword_rules = {
            "Quality": {
                "positive": ["đẹp", "tốt", "xịn", "chất", "mượt", "đẹp tuyệt vời", "tôn dáng", "thoải mái", "dày dặn", "xịn xò", "nguyên vẹn", "vượt xa mong đợi", "đồng tiền"],
                "negative": ["xấu", "hỏng", "kém", "nhái", "mỏng", "ẩu", "chỉ thừa", "rách", "bí", "không ngửi nổi", "nilon", "thất vọng", "bị rách", "ố vàng"]
            },
            "Price": {
                "positive": ["rẻ", "sale", "worth", "đáng đồng tiền", "giá tốt", "hời", "giá rẻ", "mềm"],
                "negative": ["đắt", "giá đắt", "cắt cổ", "không đáng", "lừa", "đắt đỏ", "không ngửi nổi"]
            },
            "Delivery": {
                "positive": ["nhanh", "hỏa tốc", "thần tốc", "1 ngày", "siêu nhanh", "nhanh gọn", "ship nhanh", "giao nhanh"],
                "negative": ["chậm", "rùa bò", "lâu", "hơn 1 tuần", "giao sai", "móp méo", "hộp bị"]
            },
            "Service": {
                "positive": ["nhiệt tình", "tư vấn", "thân thiện", "hỗ trợ", "dễ thương", "chu đáo", "shop chuẩn bị", "phục vụ tốt", "đổi shop hỗ trợ"],
                "negative": ["không rep", "seen", "lồi lõm", "thái độ", "không thèm", "trả lời", "tệ", "chộp giật", "không chịu"]
            }
        }

        for asp, rules in keyword_rules.items():
            pos_hits = sum(1 for w in rules["positive"] if w in lower)
            neg_hits = sum(1 for w in rules["negative"] if w in lower)

            if overall_negative:
                # Overall negative comment — positive mentions are backhanded
                if neg_hits > 0:
                    result["aspects"][asp] = {"label": 0, "text": "🔴 Chê"}
                elif pos_hits > 0:
                    # Mentioned positively but context is concessive → neutral at best
                    result["aspects"][asp] = {"label": 1, "text": "🟡 Bình thường"}
                else:
                    result["aspects"][asp] = {"label": -1, "text": "⚪ Không nhắc tới"}
            else:
                if pos_hits > neg_hits:
                    result["aspects"][asp] = {"label": 2, "text": "🟢 Khen"}
                elif neg_hits > pos_hits:
                    result["aspects"][asp] = {"label": 0, "text": "🔴 Chê"}
                elif pos_hits > 0:
                    result["aspects"][asp] = {"label": 1, "text": "🟡 Bình thường"}
                else:
                    result["aspects"][asp] = {"label": -1, "text": "⚪ Không nhắc tới"}

        return result

    def predict_single_comment(self, comment):
        """Hàm đọc và chấm điểm 1 câu bình luận"""
        # Nếu không có model thật, dùng mock
        if self.mock_mode:
            return self._mock_predict(comment)

        # Trạm 1: Làm sạch
        cleaned_text = clean_text(comment)

        result = {"original_text": comment, "aspects": {}}

        # Trạm 2: Cho từng khía cạnh chấm điểm (aspect + comment pair)
        with torch.no_grad():
            for aspect_key, aspect_text in self.aspects.items():
                inputs = self.tokenizer(
                    aspect_text,
                    cleaned_text,
                    padding="max_length",
                    truncation=True,
                    max_length=256,
                    return_tensors="pt"
                ).to(self.device)

                outputs = self.model(**inputs)
                logits = outputs.logits
                predicted_idx = torch.argmax(logits, dim=-1).item()

                result["aspects"][aspect_key] = self.label_map.get(predicted_idx, {"label": -99, "text": "Không xác định"})

        return result

# ==========================================
# KHU VỰC CHẠY THỬ NGHIỆM (TESTING)
# ==========================================
if __name__ == "__main__":
    # Khởi tạo Trạm AI (Quá trình này tốn khoảng 5-10 giây)
    print("[INFO] Dang khoi dong he thong...")
    start_time = time.time()
    ai_station = ABSAPredictor()
    print(f"[INFO] Khoi dong xong trong {round(time.time() - start_time, 2)} giay!\n")

    # Dữ liệu test
    test_comments = [
        "Áo đẹp, vải mát mẻ nhưng mà giao hàng chậm quá shop ơi",
        "Hàng fake, mỏng dính, giá đắt cắt cổ, nhắn tin shop đéo thèm rep!"
    ]

    # Bắn dữ liệu vào cho AI đọc
    print("[INFO] BAT DAU PHAN TICH:\n")
    for c in test_comments:
        ket_qua = ai_station.predict_single_comment(c)
        
        safe_print(f"Khach noi: '{ket_qua['original_text']}'")
        for aspect, data in ket_qua["aspects"].items():
            safe_print(f"   -> {aspect}: {data['text']}")
        print("-" * 40)