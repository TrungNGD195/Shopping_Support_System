import pandas as pd
import torch
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
import os
import argparse

# ==========================================
# 1. CẤU HÌNH & THAM SỐ
# ==========================================
MODEL_NAME = "vinai/phobert-base-v2"
ASPECTS = ['Quality', 'Price', 'Delivery', 'Service']
LABEL_MAPPING = {-1: 0, 0: 1, 1: 2, 2: 3}
REVERSE_LABEL_MAPPING = {v: k for k, v in LABEL_MAPPING.items()}

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    f1 = f1_score(labels, preds, average='weighted')
    acc = accuracy_score(labels, preds)
    return {'accuracy': acc, 'f1': f1}

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

def train_aspect(aspect_name, df, tokenizer, epochs=3, batch_size=4, subset=None):
    print(f"\n[INFO] Dang bat dau huan luyen cho khia canh: {aspect_name.upper()}")
    
    # Chuẩn bị dữ liệu cho khía cạnh này
    temp_df = df[['cleaned_comment', aspect_name]].dropna()
    temp_df = temp_df[temp_df[aspect_name].isin(LABEL_MAPPING.keys())]
    
    if subset:
        temp_df = temp_df.sample(min(subset, len(temp_df)), random_state=42)
        print(f"   - Su dung {len(temp_df)} mau test")

    temp_df['label'] = temp_df[aspect_name].map(LABEL_MAPPING)
    
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        temp_df['cleaned_comment'].astype(str).tolist(), 
        temp_df['label'].tolist(), 
        test_size=0.1, 
        random_state=42
    )

    train_dataset = ShoppingDataset(train_texts, train_labels, tokenizer)
    val_dataset = ShoppingDataset(val_texts, val_labels, tokenizer)

    output_dir = f'models/{aspect_name.lower()}_model'
    os.makedirs(output_dir, exist_ok=True)

    # Cấu hình huấn luyện tối ưu cho CPU/RAM thấp
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4 if batch_size < 4 else 1,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_dir='./logs',
        load_best_model_at_end=True,
        save_total_limit=1,
        fp16=torch.cuda.is_available(),
    )

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=4)
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )

    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"[SUCCESS] Da luu model {aspect_name} tai {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="ABSA Training Script")
    parser.add_argument("--aspect", type=str, default="all", help="Khía cạnh cần train (Quality, Price, Delivery, Service, all)")
    parser.add_argument("--epochs", type=int, default=3, help="Số vòng lặp huấn luyện")
    parser.add_argument("--batch", type=int, default=2, help="Kích thước batch (giảm nếu tràn RAM)")
    parser.add_argument("--subset", type=int, default=None, help="Số lượng mẫu dùng để test nhanh")
    args = parser.parse_args()

    # 1. Tải dữ liệu
    print("[INFO] Dang tai du lieu tu CSV...")
    df_pos, df_neg = None, None
    for enc in ['utf-8', 'utf-8-sig', 'latin-1']:
        try:
            if df_pos is None:
                df_pos = pd.read_csv('data/auto_labeled_cleaned_positive_reviews.csv', encoding=enc)
            if df_neg is None:
                df_neg = pd.read_csv('data/auto_labeled_cleaned_negative_reviews.csv', encoding=enc)
            print(f"[INFO] Tai thanh cong voi encoding: {enc}")
            break
        except Exception:
            df_pos, df_neg = None, None
            continue

    if df_pos is None or df_neg is None:
        print("[ERROR] Khong the doc file CSV voi bat ky encoding nao (utf-8, utf-8-sig, latin-1)")
        return

    try:
        df = pd.concat([df_pos, df_neg], ignore_index=True)
        print(f"[INFO] Tong so du lieu: {len(df)} dòng")
    except Exception as e:
        print(f"[ERROR] Loi ghep du lieu: {e}")
        return

    # 2. Tải Tokenizer
    print(f"[INFO] Dang tai Tokenizer {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # 3. Huấn luyện
    target_aspects = ASPECTS if args.aspect == "all" else [args.aspect]
    for aspect in target_aspects:
        if aspect not in ASPECTS:
            print(f"⚠️ Khía cạnh '{aspect}' không hợp lệ. Bỏ qua.")
            continue
        train_aspect(aspect, df, tokenizer, epochs=args.epochs, batch_size=args.batch, subset=args.subset)

if __name__ == "__main__":
    main()