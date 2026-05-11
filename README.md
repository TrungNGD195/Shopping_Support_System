# 🛒 Shopping Support System

Hệ thống hỗ trợ mua sắm thông minh sử dụng AI, giúp phân tích cảm xúc (Khen/Chê) từ hàng ngàn bình luận của khách hàng trên các sàn TMĐT (Shopee, Lazada, Tiki). Hệ thống cung cấp Dashboard trực quan giúp người dùng đánh giá sản phẩm trước khi mua hàng.

## 👥 Thành viên nhóm
* **Nguyễn Gia Đức Trung - B23DCVT423:** AI Core (PhoBERT), Text Preprocessing & Frontend (React)
* **Bế Quốc Khánh - B23DCCE049:** Data Crawler (Charted Sea API), Data Aggregation & Backend Logic

## 🛠 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | React 19, Vite, Tailwind CSS v4, Recharts |
| **AI/NLP** | PyTorch, HuggingFace Transformers, PhoBERT v2 |
| **Tiền xử lý** | Underthesea (Word Segmentation), Regex, Teencode Dictionary |
| **Tóm tắt** | Gemini API (Google GenAI) |
| **Crawler** | Charted Sea API, Selenium |
| **Ngôn ngữ** | Python 3.9+, JavaScript (ES Modules) |

## ⚙️ Luồng hoạt động (Pipeline)

```
[Người dùng nhập URL] → [Scraper thu thập bình luận] → [Text Preprocessing]
         ↓
[Mô hình PhoBERT ABSA phân tích] → [API trả kết quả JSON] → [Dashboard hiển thị]
         ↓
[Gemini tóm tắt ưu/nhược điểm theo từng khía cạnh]
```

1. **Input:** Người dùng dán link sản phẩm vào giao diện Web.
2. **Crawling:** Hệ thống thu thập bình luận từ sản phẩm đó.
3. **Preprocessing:** Làm sạch văn bản, chuẩn hóa tiếng Việt, dịch teencode, tách từ (underthesea).
4. **AI Inference:** Mô hình PhoBERT ABSA nhận cặp `[khía cạnh] + [bình luận]` và chấm điểm cảm xúc cho 4 khía cạnh: *Chất lượng, Giá cả, Giao hàng, Dịch vụ*.
5. **Tóm tắt:** Gemini API tổng hợp các bình luận thành đoạn tóm tắt tự nhiên cho từng khía cạnh.
6. **Output:** Dashboard hiển thị thống kê, biểu đồ, và tóm tắt ưu/nhược điểm.

## 📂 Cấu trúc dự án

```
Shopping_Support_System/
├── ai_core/                        # Scripts demo pipeline & xử lý dữ liệu
│   ├── full_pipeline_demo.py       # Demo chạy pipeline AI đầy đủ
│   ├── inference.py                # ABSAPredictor (phiên bản standalone)
│   ├── summarizer.py               # ReviewSummarizer (Gemini API)
│   ├── auto_label.py               # Gán nhãn tự động cho dữ liệu thô
│   ├── prepare_dataset.py          # Chuẩn bị dataset cho training
│   ├── preprocess_data.py          # Tiền xử lý dữ liệu gốc
│   └── kaggle_training_guide.md    # Hướng dẫn train model trên Kaggle
│
├── data/                           # Dữ liệu huấn luyện (không đẩy lên Git)
│   ├── dataset_split/              # Train/Val/Test split cho Kaggle
│   │   ├── train.csv
│   │   ├── val.csv
│   │   └── test.csv
│   ├── auto_labeled_cleaned_positive_reviews.csv
│   └── auto_labeled_cleaned_negative_reviews.csv
│
├── models/                         # Model weights đã train (không đẩy lên Git)
│   └── phobert-absa-final/         # Mô hình ABSA (aspect+comment pair)
│       ├── model.safetensors
│       ├── config.json
│       ├── vocab.txt
│       └── bpe.codes
│
├── src/
│   ├── api_server.py               # FastAPI REST API (Entry Point chính)
│   ├── inference.py                # Class ABSAPredictor - nạp & chạy model
│   ├── scraper.py                  # Thu thập bình luận từ URL sản phẩm
│   ├── train_absa.py               # Script huấn luyện model PhoBERT
│   │
│   ├── frontend/                   # React Web App (Vite + Tailwind v4)
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── Home.jsx        # Trang chủ - nhập URL sản phẩm
│   │   │   │   └── Dashboard.jsx   # Dashboard phân tích kết quả
│   │   │   ├── App.jsx             # Router chính
│   │   │   ├── main.jsx            # Entry point React
│   │   │   └── index.css           # Design system (Tailwind v4)
│   │   └── package.json
│   │
│   └── utils/                      # Module hỗ trợ xử lý ngôn ngữ
│       ├── text_processing.py      # Hàm clean_text (teencode, tách từ, v.v.)
│       └── teencode_miner.py       # Bộ từ điển teencode
│
├── .gitignore
├── colab_train_absa.ipynb          # Notebook train 4 model riêng trên Colab
├── README.md
└── requirements.txt
```

## 🚀 Hướng dẫn cài đặt & chạy

### Yêu cầu
- Python 3.9+ (khuyến nghị 3.12/3.13)
- Node.js 18+
- Model weights `phobert-absa-final` trong thư mục `models/`

### Bước 1: Clone & cài thư viện

```bash
# Clone repo
git clone https://github.com/TrungNGD195/Shopping_Support_System.git
cd Shopping_Support_System

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Cài đặt thư viện Python
pip install -r requirements.txt

# Cài đặt thư viện Frontend
cd src/frontend && npm install && cd ../..
```

### Bước 2: Tải & giải nén mô hình AI

Mô hình PhoBERT ABSA (`phobert-absa-final`) được huấn luyện trên Kaggle với kỹ thuật **Text-Pair Classification** — ghép cặp `[khía cạnh] </s> [bình luận]` để dự đoán cảm xúc.

**Tải mô hình:**
```bash
# Tải file phobert-absa-final.zip từ GitHub Releases hoặc link chia sẻ
# Đặt file vào thư mục models/

# Giải nén
mkdir -p models/phobert-absa-final
unzip models/phobert-absa-final.zip -d models/phobert-absa-final/
```

Sau khi giải nén, cấu trúc thư mục `models/` phải như sau:
```
models/
└── phobert-absa-final/
    ├── model.safetensors      # Trọng số mô hình (~519MB)
    ├── config.json            # Cấu hình mô hình
    ├── vocab.txt              # Từ vựng PhoBERT
    ├── bpe.codes              # BPE tokenizer
    ├── tokenizer_config.json
    └── added_tokens.json
```

> **Lưu ý:** File model.safetensors (~519MB) quá lớn để đẩy lên Git. Sử dụng GitHub Releases hoặc Google Drive để chia sẻ file.

### Bước 3: Cấu hình Gemini API (Tùy chọn)

Để bật tính năng tóm tắt bình luận bằng Gemini:
```bash
# Tạo file .env trong thư mục ai_core/
echo "GEMINI_API_KEY=your_api_key_here" > ai_core/.env
```

Lấy API key tại: https://aistudio.google.com/apikey

### Bước 4: Chạy hệ thống

**Cách 1: Chạy tự động (PowerShell)**
```powershell
.\run_app.ps1
```

**Cách 2: Chạy thủ công**
```bash
# Terminal 1 - Backend (API)
source venv/bin/activate
cd src && python api_server.py

# Terminal 2 - Frontend (React)
cd src/frontend && npm run dev
```

Sau khi khởi động:
- 🌐 **Web App:** http://localhost:5173
- 📡 **API Docs:** http://localhost:8000/docs

### Bước 5: Chạy demo pipeline (Tùy chọn)

```bash
source venv/bin/activate
python ai_core/full_pipeline_demo.py
```

Script sẽ tự động đọc dữ liệu từ `data/`, chạy mô hình ABSA, và gọi Gemini để tóm tắt kết quả.

## 🧠 Huấn luyện mô hình

### Cách 1: Kaggle (Khuyến nghị — Text-Pair ABSA)

Huấn luyện **1 mô hình duy nhất** cho tất cả 4 khía cạnh bằng kỹ thuật Text-Pair Classification:

1. Upload thư mục `data/dataset_split/` lên Kaggle
2. Bật GPU T4 hoặc P100
3. Làm theo hướng dẫn trong `ai_core/kaggle_training_guide.md`
4. Tải `phobert-absa-final.zip` về và giải nén vào `models/phobert-absa-final/`

### Cách 2: Google Colab (4 mô hình riêng biệt)

Huấn luyện **4 mô hình riêng** (mỗi mô hình cho 1 khía cạnh):

1. Upload `colab_train_absa.ipynb` lên Google Colab
2. Chọn Runtime → GPU (T4)
3. Upload 2 file CSV từ thư mục `data/`
4. Chạy tất cả các ô → Tải `trained_models.zip` về
5. Giải nén vào thư mục `models/`

### Cách 3: Train local

```bash
python src/train_absa.py --aspect Quality --batch 2
python src/train_absa.py --aspect Price --batch 2
python src/train_absa.py --aspect Delivery --batch 2
python src/train_absa.py --aspect Service --batch 2
```

## 📊 Hệ thống nhãn ABSA

Mô hình sử dụng 4 nhãn cho mỗi khía cạnh:

| Giá trị | Ý nghĩa | Mô tả |
|---------|---------|-------|
| `0` | Tiêu cực (Chê) | Khách hàng phàn nàn, không hài lòng |
| `1` | Trung lập | Nhận xét bình thường, không rõ xu hướng |
| `2` | Tích cực (Khen) | Khách hàng hài lòng, khen ngợi |
| `3` | Không nhắc tới | Bình luận không đề cập khía cạnh này |

Input của mô hình dạng cặp: `<s> khía cạnh </s></s> bình luận </s>`

Ví dụ: `<s> chất lượng </s></s> áo đẹp tuyệt_vời chất_liệu xịn_xò </s>` → dự đoán: `2 (Khen)`