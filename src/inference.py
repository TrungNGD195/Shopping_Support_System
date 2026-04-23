import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import time

# Tạm thời import hàm clean_text, nếu chưa có file này thì dùng hàm mộc
try:
    from utils.text_processing import clean_text
except ImportError:
    # Hàm dự phòng nếu chưa nối file utils
    def clean_text(text): return text.lower().strip()

class ABSAPredictor:
    """
    Class này đóng vai trò là Trạm Trí Tuệ. 
    Nó sẽ nạp 4 mô hình vào RAM 1 lần duy nhất khi khởi tạo.
    """
    def __init__(self):
        # 1. Xác định thiết bị (Ưu tiên dùng Card đồ họa GPU nếu có, không thì chạy CPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 Đang khởi động AI trên thiết bị: {self.device}")

        # 2. Load bộ phân giải từ vựng (Tokenizer) của PhoBERT
        # (Chỉ cần load 1 cái dùng chung cho cả 4 mô hình)
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)

        # 3. Đường dẫn đến 4 "bộ não"
        self.model_paths = {
            "Quality": "models/quality_model/checkpoint-6",
            "Price": "models/price_model/checkpoint-6",
            # "Delivery": "models/delivery_model/checkpoint-6",
            # "Service": "models/service_model/checkpoint-6"
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
                print(f"✅ Đã nạp thành công mô hình: {aspect}")
            except Exception as e:
                print(f"⚠️ Chưa tìm thấy hoặc lỗi load mô hình {aspect} tại {path}")

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
                result["aspects"][aspect] = self.label_map.get(predicted_idx, "Unknown")
                
        return result

# ==========================================
# KHU VỰC CHẠY THỬ NGHIỆM (TESTING)
# ==========================================
if __name__ == "__main__":
    # Khởi tạo Trạm AI (Quá trình này tốn khoảng 5-10 giây)
    print("⏳ Đang khởi động hệ thống...")
    start_time = time.time()
    ai_station = ABSAPredictor()
    print(f"⏱️ Khởi động xong trong {round(time.time() - start_time, 2)} giây!\n")

    # Dữ liệu test
    test_comments = [
        "Áo đẹp, vải mát mẻ nhưng mà giao hàng chậm quá shop ơi",
        "Hàng fake, mỏng dính, giá đắt cắt cổ, nhắn tin shop đéo thèm rep!"
    ]

    # Bắn dữ liệu vào cho AI đọc
    print("🔍 BẮT ĐẦU PHÂN TÍCH:\n")
    for c in test_comments:
        ket_qua = ai_station.predict_single_comment(c)
        
        print(f"📝 Khách nói: '{ket_qua['original_text']}'")
        for aspect, data in ket_qua["aspects"].items():
            print(f"   👉 {aspect}: {data['text']}")
        print("-" * 40)