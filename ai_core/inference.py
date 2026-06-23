import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import transformers
import os

transformers.logging.set_verbosity_error()
class ABSAPredictor:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading model from: {model_path} to {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)
        
        self.aspects = {
            'Quality': 'chất lượng',
            'Price': 'giá cả',
            'Delivery': 'giao hàng',
            'Service': 'dịch vụ'
        }
        
        self.label_map = {
            0: "Tiêu cực (Chê)",
            1: "Bình thường",
            2: "Tích cực (Khen)",
            3: "Không nhắc tới"
        }

    def predict(self, comment):
        results = {}
        aspect_keys = list(self.aspects.keys())
        aspect_texts = [self.aspects[k] for k in aspect_keys]
        comments_repeated = [comment] * len(aspect_texts)
        
        inputs = self.tokenizer(
            aspect_texts, 
            comments_repeated, 
            padding="max_length", 
            truncation=True, 
            max_length=128, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            predicted_classes = torch.argmax(logits, dim=-1).tolist()
            
            for i, aspect_key in enumerate(aspect_keys):
                results[aspect_key] = self.label_map[predicted_classes[i]]
                
        return results

    def predict_batch(self, comments, batch_size=64):
        """Dự đoán cả một danh sách comments cùng lúc (Batch Inference) để tăng tốc 5-10 lần"""
        if not comments: return []
        
        aspect_keys = list(self.aspects.keys())
        aspect_texts = [self.aspects[k] for k in aspect_keys]
        
        all_aspects = []
        all_comments = []
        for cmt in comments:
            all_aspects.extend(aspect_texts)
            all_comments.extend([cmt] * len(aspect_texts))
                
        all_predicted_classes = []
        
        for i in range(0, len(all_comments), batch_size):
            batch_aspects = all_aspects[i:i+batch_size]
            batch_comments = all_comments[i:i+batch_size]
            
            inputs = self.tokenizer(
                batch_aspects, 
                batch_comments, 
                padding=True,
                truncation=True, 
                max_length=128, 
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                preds = torch.argmax(outputs.logits, dim=-1).tolist()
                all_predicted_classes.extend(preds)
                
        results = []
        idx = 0
        for _ in comments:
            res = {}
            for aspect_key in aspect_keys:
                res[aspect_key] = self.label_map[all_predicted_classes[idx]]
                idx += 1
            results.append(res)
            
        return results

class SpamPredictor:
    def __init__(self, model_path="models/phobert_spam"):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
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
            
        return predicted_class == 0

if __name__ == "__main__":
    model_dir = r"d:\Shopping_Support_System\models\phobert-absa-final"
    
    if not os.path.exists(model_dir):
        print(f"LỖI: Không tìm thấy thư mục mô hình tại: {model_dir}")
        print("Vui lòng tạo thư mục 'models' trong project và giải nén file zip vào đó!")
    else:
        predictor = ABSAPredictor(model_dir)
        
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
