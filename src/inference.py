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
    Nó sẽ nạp 4 mô hình vào RAM 1 lần duy nhất khi khởi tạo.
    """
    def __init__(self):
        # 1. Xác định thiết bị (Ưu tiên dùng Card đồ họa GPU nếu có, không thì chạy CPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        safe_print(f"[INFO] Dang khoi dong AI tren thiet bi: {self.device}")

        # 2. Load bộ phân giải từ vựng (Tokenizer) của PhoBERT
        # (Chỉ cần load 1 cái dùng chung cho cả 4 mô hình)
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)

        # 3. Đường dẫn đến 4 "bộ não"
        self.model_paths = {
            "Quality": "models/quality_model",
            "Price": "models/price_model",
            "Delivery": "models/delivery_model",
            "Service": "models/service_model"
        }

        self.models = {}
        self.mock_mode = False

        # 4. Nạp cả 4 mô hình lên RAM
        for aspect, path in self.model_paths.items():
            try:
                # use_safetensors=True để đọc chuẩn định dạng mới
                model = AutoModelForSequenceClassification.from_pretrained(path, use_safetensors=True)
                model.to(self.device)
                model.eval() # Chuyển sang chế độ Chấm điểm (Không học nữa)
                self.models[aspect] = model
                safe_print(f"[SUCCESS] Da nap thanh cong mo hinh: {aspect}")
            except Exception as e:
                safe_print(f"[WARNING] Chua tim thay hoac loi load mo hinh {aspect} tai {path}")

        # Fallback: nếu không có model nào, dùng keyword-based mock
        if not self.models:
            self.mock_mode = True
            safe_print("[INFO] Khong tim thay mo hinh nao. Chuyen sang che do MO MOCK (keyword-based).")

        # 5. Bộ từ điển dịch nhãn máy tính ra tiếng người cho dễ hiểu
        # Giả định lúc train bạn map: 0 -> -1, 1 -> 0, 2 -> 1, 3 -> 2
        self.label_map = {
            0: {"label": -1, "text": "⚪ Không nhắc tới"},
            1: {"label": 0,  "text": "🔴 Chê"},
            2: {"label": 1,  "text": "🟡 Bình thường"},
            3: {"label": 2,  "text": "🟢 Khen"}
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

        # Biến chữ thành số cho AI đọc
        inputs = self.tokenizer(cleaned_text, return_tensors="pt", truncation=True, max_length=256)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        result = {"original_text": comment, "aspects": {}}

        # Trạm 2: Cho 4 mô hình lần lượt chấm điểm
        with torch.no_grad(): # Tắt tính năng tự học để tăng tốc độ dự đoán x5 lần
            for aspect, model in self.models.items():
                outputs = model(**inputs)
                logits = outputs.logits
                predicted_idx = torch.argmax(logits, dim=1).item()

                # Dịch kết quả
                result["aspects"][aspect] = self.label_map.get(predicted_idx, {"label": -99, "text": "Không xác định"})

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