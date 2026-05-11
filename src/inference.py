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

        # 5. Bộ từ điển dịch nhãn máy tính ra tiếng người cho dễ hiểu
        # Giả định lúc train bạn map: 0 -> -1, 1 -> 0, 2 -> 1, 3 -> 2
        self.label_map = {
            0: {"label": -1, "text": "⚪ Không nhắc tới"},
            1: {"label": 0,  "text": "🔴 Chê"},
            2: {"label": 1,  "text": "🟡 Bình thường"},
            3: {"label": 2,  "text": "🟢 Khen"}
        }

    def predict_single_comment(self, comment):
        """Hàm đọc và chấm điểm 1 câu bình luận"""
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