# Hướng dẫn Huấn luyện PhoBERT cho ABSA trên Kaggle

Dự án của bạn là **Aspect-Based Sentiment Analysis (ABSA)** với 4 khía cạnh: `Quality`, `Price`, `Delivery`, `Service`. Mỗi khía cạnh có 4 nhãn:
- `2`: Tích cực
- `1`: Bình thường
- `0`: Tiêu cực
- `-1`: Không nhắc tới

Thay vì huấn luyện 4 mô hình riêng biệt (rất tốn thời gian), chúng ta sẽ sử dụng kỹ thuật **Text-Pair Classification** (Ghép cặp văn bản). 
Cụ thể, input đưa vào PhoBERT sẽ có dạng: `[Khía cạnh] </s> [Nội dung bình luận]`. Mô hình chỉ cần dự đoán 1 trong 4 nhãn cho cặp văn bản này. Kỹ thuật này chuẩn xác và rất dễ code.

---

## Bước 1: Chuẩn bị trên Kaggle
1. Tạo một Notebook mới trên [Kaggle](https://www.kaggle.com/).
2. Bật **GPU T4 x2** hoặc **P100** trong phần Settings (góc phải màn hình) để train nhanh hơn.
3. Ở menu bên phải, phần **Input**, click `Upload Data` -> Đẩy thư mục `dataset_split/` (chứa `train.csv`, `val.csv`, `test.csv`) lên Kaggle.

---

## Bước 2: Cài đặt thư viện (Chạy ở Cell 1)

```python
!pip install transformers datasets evaluate pyvi
```

---

## Bước 3: Code Huấn luyện (Copy vào Cell 2 và chạy)

Đoạn code dưới đây sẽ tự động load data, chuyển đổi định dạng cặp văn bản (Text-Pair) và huấn luyện bằng Hugging Face Trainer.

```python
import pandas as pd
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import numpy as np
import evaluate

# 1. Định nghĩa hàm biến đổi dữ liệu
def flatten_dataset(csv_path):
    df = pd.read_csv(csv_path)
    aspects = {
        'Quality': 'chất lượng',
        'Price': 'giá cả',
        'Delivery': 'giao hàng',
        'Service': 'dịch vụ'
    }
    
    new_data = []
    for _, row in df.iterrows():
        comment = str(row['cleaned_comment'])
        for asp_key, asp_text in aspects.items():
            # Chuyển nhãn -1 thành 3 (do PyTorch yêu cầu label từ 0 -> N-1)
            # 0: Tiêu cực, 1: Bình thường, 2: Tích cực, 3: Không nhắc tới
            label = int(row[asp_key])
            if label == -1:
                label = 3
                
            new_data.append({
                'text': comment,
                'aspect': asp_text,
                'label': label
            })
            
    return pd.DataFrame(new_data)

# Thay đường dẫn này bằng đường dẫn dataset bạn vừa upload lên Kaggle
# Ví dụ: '/kaggle/input/shopping-dataset/'
DATA_DIR = '/kaggle/input/shopping-dataset/' 

print("Đang xử lý dữ liệu...")
train_df = flatten_dataset(DATA_DIR + 'train.csv')
val_df = flatten_dataset(DATA_DIR + 'val.csv')
test_df = flatten_dataset(DATA_DIR + 'test.csv')

# Chuyển đổi sang định dạng Hugging Face Dataset
dataset = DatasetDict({
    'train': Dataset.from_pandas(train_df),
    'validation': Dataset.from_pandas(val_df),
    'test': Dataset.from_pandas(test_df)
})

# 2. Tokenize dữ liệu với PhoBERT
model_checkpoint = "vinai/phobert-base"
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

def tokenize_function(examples):
    # Ghép aspect và text: <s> aspect </s></s> text </s>
    return tokenizer(
        examples["aspect"], 
        examples["text"], 
        padding="max_length", 
        truncation=True, 
        max_length=128
    )

print("Đang Tokenize dữ liệu...")
tokenized_datasets = dataset.map(tokenize_function, batched=True)

# 3. Định nghĩa Metrics (Accuracy & F1)
metric_acc = evaluate.load("accuracy")
metric_f1 = evaluate.load("f1")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = metric_acc.compute(predictions=predictions, references=labels)
    f1 = metric_f1.compute(predictions=predictions, references=labels, average="macro")
    return {"accuracy": acc["accuracy"], "f1_macro": f1["f1"]}

# 4. Tải Model PhoBERT
# Số lượng nhãn là 4 (0, 1, 2, 3)
model = AutoModelForSequenceClassification.from_pretrained(model_checkpoint, num_labels=4)

# 5. Cấu hình Tham số Huấn luyện
training_args = TrainingArguments(
    output_dir="/kaggle/working/phobert-absa",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=3,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    report_to="none" # Tắt wandb nếu không dùng
)

# 6. Khởi tạo Trainer và Huấn luyện
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    compute_metrics=compute_metrics,
)

print("Bắt đầu huấn luyện...")
trainer.train()

# 7. Đánh giá trên tập Test
print("Đánh giá trên tập Test:")
test_results = trainer.evaluate(tokenized_datasets["test"])
print(test_results)

# 8. Lưu mô hình
trainer.save_model("/kaggle/working/phobert-absa-final")
tokenizer.save_pretrained("/kaggle/working/phobert-absa-final")
print("Đã lưu mô hình thành công!")
```

---

## Bước 4: Tải mô hình về
Sau khi huấn luyện xong (mất khoảng 20-30 phút), mô hình sẽ được lưu trong thư mục `/kaggle/working/phobert-absa-final`.

**Code nén thư mục để tải về (Chạy ở Cell 3):**
```python
import shutil
shutil.make_archive("/kaggle/working/phobert-absa-final", 'zip', "/kaggle/working/phobert-absa-final")
```
Sau đó bạn ở cột bên phải, phần Output, làm mới (refresh) rồi tải file `phobert-absa-final.zip` về máy tính. File này sẽ chứa các file `config.json`, `pytorch_model.bin`, `vocab.txt`,... dùng để đưa vào giao diện Streamlit.
