import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
import os

# ==========================================
# 1. CHUẨN BỊ DỮ LIỆU (DUMMY DATA)
# ==========================================
# Dữ liệu này giả định đã được chạy qua hàm clean_text() của bạn (đã tách từ bằng dấu _)
dummy_data = {
    'comment_clean': [
        "áo đẹp lắm vải mát", 
        "hàng fake mỏng dính", 
        "giao_hàng siêu nhanh", 
        "chất_lượng bình_thường đúng giá_tiền", 
        "form xấu rụng rốn", 
        "xịn_sò đáng tiền mua nha"
    ],
    'Quality': [2, 0, -1, 1, 0, 2], # Nhãn thực tế của cột Chất lượng
    'Price': [-1, -1, -1, 1, -1, 2] # Nhãn thực tế của cột Giá cả
}
df = pd.DataFrame(dummy_data)

# CHỌN CỘT ĐỂ HUẤN LUYỆN (Chỉ cần đổi tên cột ở đây là train được mô hình khác)
TARGET_COLUMN = 'Price'

# --- BƯỚC ÉP KIỂU NHÃN (CỰC QUAN TRỌNG) ---
# AI của HuggingFace bắt buộc nhãn phải bắt đầu từ 0 (0, 1, 2, 3)
# Ta phải dịch từ hệ thống của nhóm (-1, 0, 1, 2) sang hệ thống của máy
label_mapping = {-1: 0, 0: 1, 1: 2, 2: 3}
df['label'] = df[TARGET_COLUMN].map(label_mapping)

# ==========================================
# 2. KHỞI TẠO PHOVERT TỪ HUGGINGFACE
# ==========================================
model_name = "vinai/phobert-base-v2"
print(f"⏳ Đang tải Tokenizer từ {model_name}...")
tokenizer = AutoTokenizer.from_pretrained(model_name)

# ==========================================
# 3. CHUYỂN ĐỔI DỮ LIỆU SANG ĐỊNH DẠNG TENSOR (PYTORCH)
# ==========================================
class ShoppingDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]

        # Tokenizer sẽ băm câu văn thành các con số ma trận
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# Chia tập Train/Test (80% học, 20% thi thử)
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['comment_clean'].tolist(), 
    df['label'].tolist(), 
    test_size=0.2, 
    random_state=42
)

train_dataset = ShoppingDataset(train_texts, train_labels, tokenizer)
val_dataset = ShoppingDataset(val_texts, val_labels, tokenizer)

# ==========================================
# 4. TẢI MÔ HÌNH VÀ CẤU HÌNH HUẤN LUYỆN
# ==========================================
print("⏳ Đang tải kiến trúc mạng nơ-ron PhoBERT...")
# num_labels=4 vì chúng ta có 4 trạng thái (-1, 0, 1, 2)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=4)

# Tạo thư mục lưu model nếu chưa có
output_dir = f'models/{TARGET_COLUMN.lower()}_model'
os.makedirs(output_dir, exist_ok=True)

training_args = TrainingArguments(
    output_dir=output_dir,                # Nơi lưu cục tạ (weights)
    num_train_epochs=3,                   # Số lần lặp qua toàn bộ dữ liệu
    per_device_train_batch_size=2,        # Số câu học cùng lúc (Máy yếu thì để 2 hoặc 4)
    per_device_eval_batch_size=2,
    eval_strategy="epoch",                # Thi thử sau mỗi vòng học
    save_strategy="epoch",                # Lưu lại model sau mỗi vòng học
    logging_dir='./logs',
    load_best_model_at_end=True,          # Giữ lại phiên bản xịn nhất
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

# ==========================================
# 5. KÍCH HOẠT QUÁ TRÌNH HỌC
# ==========================================
if __name__ == "__main__":
    print(f"🔥 Bắt đầu huấn luyện mô hình cho khía cạnh: {TARGET_COLUMN.upper()}")
    trainer.train()
    print(f"✅ Hoàn tất! File trọng số đã được lưu an toàn tại thư mục '{output_dir}'")