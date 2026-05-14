import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import transformers
import os

# Tắt cảnh báo rác (ví dụ: overflowing tokens) của transformers để terminal sạch sẽ
transformers.logging.set_verbosity_error()
class ABSAPredictor:
    def __init__(self, model_path):
        # Tự động chọn GPU nếu có, nếu không thì dùng CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading model from: {model_path} to {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)
        
        # 4 Khía cạnh cần đánh giá
        self.aspects = {
            'Quality': 'chất lượng',
            'Price': 'giá cả',
            'Delivery': 'giao hàng',
            'Service': 'dịch vụ'
        }
        
        # Map số sang chữ cho dễ đọc theo đúng colab_train_absa.ipynb
        # {-1: 3, 0: 0, 1: 1, 2: 2} => 0=Chê, 1=Bình thường, 2=Khen, 3=Không nhắc tới
        self.label_map = {
            0: "Tiêu cực (Chê)",
            1: "Bình thường",
            2: "Tích cực (Khen)",
            3: "Không nhắc tới"
        }

    def predict(self, comment):
        results = {}
        for aspect_key, aspect_text in self.aspects.items():
            # Ghép cặp: "chất lượng </s> bình luận"
            inputs = self.tokenizer(
                aspect_text, 
                comment, 
                padding="max_length", 
                truncation=True, 
                max_length=128, 
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                predicted_class = torch.argmax(logits, dim=-1).item()
                
                results[aspect_key] = self.label_map[predicted_class]
                
        return results

class SpamPredictor:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Đang tải mô hình Spam Filter từ: {model_path} lên {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)

    def is_spam(self, comment):
        inputs = self.tokenizer(
            comment, 
            padding="max_length", 
            truncation=True, 
            max_length=128, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predicted_class = torch.argmax(outputs.logits, dim=-1).item()
            
        # Trong data train: 0 là Spam, 1 là Hợp lệ. Vì vậy trả về True nếu là Spam (0)
        return predicted_class == 0

if __name__ == "__main__":
    # Đường dẫn cố định tới thư mục giải nén model
    model_dir = r"d:\Shopping_Support_System\models\phobert-absa-gemma"
    
    if not os.path.exists(model_dir):
        print(f"LỖI: Không tìm thấy thư mục mô hình tại: {model_dir}")
        print("Vui lòng tạo thư mục 'models' trong project và giải nén file zip vào đó!")
    else:
        # Khởi tạo mô hình
        predictor = ABSAPredictor(model_dir)
        
        # Danh sách nhiều câu bình luận Test thử
        test_comments = [
            "Điện thoại xài rất mượt, màn hình đẹp nhưng shop đóng gói sơ sài hộp bị móp méo, nhắn tin không thèm trả lời.",
            "Giá thì quá đắt so với chất lượng, xài được 2 ngày đã hỏng. Giao hàng rùa bò.",
            "Shop tư vấn vô cùng nhiệt tình dễ thương, giao siêu hỏa tốc trong 2h, sản phẩm cầm rất đầm tay và xịn xò nha mọi người, đáng đồng tiền bát gạo!",
            "Chất lượng bình thường, không có gì nổi trội. Shipper thái độ lồi lõm ném hàng vào sân.",
            "Mua săn sale rẻ bèo mà ốp lưng ố vàng hết trơn, chán chả buồn nói."
        ]
        
        for i, test_comment in enumerate(test_comments, 1):
            print(f"\n[{i}/Bình luận]: '{test_comment}'")
            print("-" * 50)
            
            predictions = predictor.predict(test_comment)
            for aspect, sentiment in predictions.items():
                print(f"- {aspect:10} : {sentiment}")
