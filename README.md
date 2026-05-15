# 🛒 Hệ Thống Hỗ Trợ Mua Sắm Thông Minh (Shopping Support System)

Ứng dụng thực tiễn của **NLP (Xử lý ngôn ngữ tự nhiên)** và **LLM (Mô hình ngôn ngữ lớn)** vào bài toán **ABSA (Aspect-Based Sentiment Analysis - Phân tích cảm xúc theo khía cạnh)**. Hệ thống tự động trích xuất bình luận từ các sàn TMĐT (Shopee, Tiki), ứng dụng mô hình **Google Gemma** để gán nhãn dữ liệu tự động (Auto-labeling) & lọc rác, sau đó dùng mô hình **PhoBERT** để phân loại cảm xúc (Khen/Chê/Trung lập) cho 4 khía cạnh: Chất lượng, Giá cả, Giao hàng, Dịch vụ. Cuối cùng, API của **Google Gemini** được sử dụng để tóm tắt thông minh. Tất cả được trình bày qua một Web Dashboard hiện đại.

## 👥 Đội Ngũ Phát Triển

Dự án được phân chia khối lượng công việc đồng đều, kết hợp chặt chẽ giữa kỹ thuật nền tảng và trải nghiệm người dùng:

* **Bế Quốc Khánh (B23DCCE049) — Lead Backend & AI Core**
  * **AI Core & Training:** Ứng dụng Google Gemma để gán nhãn dữ liệu tự động (Auto-labeling), sau đó trực tiếp huấn luyện mô hình cốt lõi PhoBERT ABSA bằng kỹ thuật Text-Pair Classification trên môi trường máy chủ (Kaggle/Colab).
  * **System Architecture:** Thiết kế và phát triển toàn bộ kiến trúc API Backend bằng FastAPI, đảm bảo luồng xử lý dữ liệu tốc độ cao.
  * **Data & AI Integration:** Xây dựng Data Pipeline lọc rác (Spam Filter), đồng thời tích hợp trọng số PhoBERT và Gemini API vào luồng suy luận tự động.

* **Nguyễn Gia Đức Trung (B23DCVT423) — Lead Frontend & UI/UX**
  * **Frontend Architecture:** Cấu trúc toàn bộ nền tảng Single Page Application (SPA) bằng React 19 và Vite, quản lý luồng State dữ liệu phức tạp.
  * **Data Visualization:** Xây dựng hệ thống biểu đồ tương tác cấp cao (Recharts) nhằm biểu diễn trực quan các lát cắt thống kê cảm xúc đa chiều.
  * **UI/UX & Design System:** Thiết kế trải nghiệm người dùng hiện đại, xây dựng hệ thống Design System nhất quán thông qua Tailwind CSS v4.
  * **Performance Optimization:** Tối ưu hóa hiệu năng phía người dùng (Client-side Rendering) và xử lý bất đồng bộ (Async) mượt mà khi hệ thống tải dữ liệu AI.

## 🛠 Công Nghệ Sử Dụng

| Thành phần | Công nghệ cốt lõi |
|---|---|
| **Backend** | FastAPI, Uvicorn, Python 3.9+ |
| **Frontend** | React 19, Vite, Tailwind CSS v4, Recharts |
| **AI / Machine Learning** | PyTorch, HuggingFace, PhoBERT v2 (ABSA), Google Gemma (Auto-labeling) |
| **LLM & Summarization** | Google GenAI (Gemini API), Prompt Engineering |
| **Data Processing** | Pandas, Regex Toolkit |

## ⚙️ Luồng hoạt động (Pipeline)

```
[Người dùng nhập URL] → [Trích xuất dữ liệu & Lọc Spam]
         ↓
[Mô hình PhoBERT ABSA phân tích] → [API trả kết quả JSON] → [Dashboard hiển thị]
         ↓
[Gemini tóm tắt ưu/nhược điểm theo từng khía cạnh]
```

1. **Input:** Người dùng dán link sản phẩm vào giao diện Web.
2. **Data Extraction:** Hệ thống trích xuất bình luận của sản phẩm tương ứng từ tập dữ liệu (Dataset).
3. **Spam Filtering:** Lọc bỏ các bình luận rác, đánh giá lấy xu, nội dung vô nghĩa bằng thuật toán Heuristic.
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