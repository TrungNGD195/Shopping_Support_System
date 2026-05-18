import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
import os

# 1. Dataset Class
class SpamDataset(Dataset):
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

def train_spam_model():
    print("[1] Đang tải dữ liệu từ data/spam_dataset.csv...")
    if not os.path.exists("data/spam_dataset.csv"):
        print("LỖI: Chưa có file data/spam_dataset.csv! Hãy chạy auto_label_spam_gemini.py trước.")
        return

    df = pd.read_csv("data/spam_dataset.csv")
    
    # 2. Chia tập Train/Test
    X_train, X_test, y_train, y_test = train_test_split(df['comment'], df['is_spam'], test_size=0.1, random_state=42)

    # 3. Khởi tạo Tokenizer và PhoBERT
    print("[2] Đang tải mô hình PhoBERT-base...")
    tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)
    # 2 Nhãn: 0 (Spam) và 1 (Review thật)
    model = AutoModelForSequenceClassification.from_pretrained("vinai/phobert-base", num_labels=2)

    # 4. Chuẩn bị Dataset
    train_dataset = SpamDataset(X_train.tolist(), y_train.tolist(), tokenizer)
    test_dataset = SpamDataset(X_test.tolist(), y_test.tolist(), tokenizer)

    # 5. Cấu hình Training
    training_args = TrainingArguments(
        output_dir='./results_spam',
        num_train_epochs=3,              # Train 3 vòng
        per_device_train_batch_size=8,   # Batch size nhỏ cho đỡ tốn RAM
        per_device_eval_batch_size=8,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir='./logs_spam',
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
    )

    # 6. Bắt đầu Train
    print("[3] Bắt đầu quá trình Huấn Luyện (Training)...")
    trainer.train()

    # 7. Lưu mô hình
    print("[4] Đang lưu mô hình vào thư mục models/phobert-spam-filter...")
    model.save_pretrained("models/phobert-spam-filter")
    tokenizer.save_pretrained("models/phobert-spam-filter")
    print("HOÀN TẤT! Đã train xong AI Lọc Spam.")

if __name__ == "__main__":
    train_spam_model()
