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
| **Crawler** | Charted Sea API, Selenium |
| **Ngôn ngữ** | Python 3.9+, JavaScript (ES Modules) |

## ⚙️ Luồng hoạt động (Pipeline)

```
[Người dùng nhập URL] → [Scraper thu thập bình luận] → [Text Preprocessing]
         ↓
[4 mô hình PhoBERT phân tích] → [API trả kết quả JSON] → [Dashboard hiển thị]
```

1. **Input:** Người dùng dán link sản phẩm vào giao diện Web.
2. **Crawling:** Hệ thống thu thập bình luận từ sản phẩm đó.
3. **Preprocessing:** Làm sạch văn bản, chuẩn hóa tiếng Việt, dịch teencode, tách từ.
4. **AI Inference:** 4 mô hình PhoBERT chấm điểm cảm xúc cho 4 khía cạnh: *Chất lượng, Giá cả, Giao hàng, Dịch vụ*.
5. **Output:** Dashboard hiển thị thống kê và tóm tắt ưu/nhược điểm.

## 📂 Cấu trúc dự án

```
Shopping_Support_System/
├── ai_core/                    # Scripts tiền xử lý & gán nhãn dữ liệu
│   ├── auto_label.py           # Gán nhãn tự động cho dữ liệu thô
│   ├── prepare_dataset.py      # Chuẩn bị dataset cho training
│   └── preprocess_data.py      # Tiền xử lý dữ liệu gốc
│
├── data/                       # Dữ liệu huấn luyện (không đẩy lên Git)
│   ├── auto_labeled_cleaned_positive_reviews.csv
│   ├── auto_labeled_cleaned_negative_reviews.csv
│   ├── positive_reviews.csv
│   └── negative_reviews.csv
│
├── models/                     # Model weights đã train (không đẩy lên Git)
│   ├── quality_model/          # Mô hình đánh giá Chất lượng
│   ├── price_model/            # Mô hình đánh giá Giá cả
│   ├── delivery_model/         # Mô hình đánh giá Giao hàng
│   └── service_model/          # Mô hình đánh giá Dịch vụ
│
├── src/
│   ├── api_server.py           # FastAPI REST API (Entry Point chính)
│   ├── inference.py            # Class ABSAPredictor - nạp & chạy 4 model
│   ├── scraper.py              # Thu thập bình luận từ URL sản phẩm
│   ├── train_absa.py           # Script huấn luyện model PhoBERT
│   │
│   ├── crawler/                # Scripts thu thập dữ liệu từ sàn TMĐT
│   │   ├── scripts/            # Các script crawl review
│   │   └── API Reference _ Charted Sea.pdf
│   │
│   ├── frontend/               # React Web App (Vite + Tailwind v4)
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── Home.jsx    # Trang chủ - nhập URL sản phẩm
│   │   │   │   └── Dashboard.jsx  # Dashboard phân tích kết quả
│   │   │   ├── App.jsx         # Router chính
│   │   │   ├── main.jsx        # Entry point React
│   │   │   └── index.css       # Design system (Tailwind v4)
│   │   └── package.json
│   │
│   └── utils/                  # Module hỗ trợ xử lý ngôn ngữ
│       ├── text_processing.py  # Hàm clean_text (teencode, tách từ, v.v.)
│       └── teencode_miner.py   # Bộ từ điển teencode
│
├── .gitignore
├── colab_train_absa.ipynb      # Notebook train model trên Google Colab (GPU)
├── LABELING_GUIDE.md           # Quy tắc gán nhãn dữ liệu (-1, 0, 1, 2)
├── README.md
├── requirements.txt
└── run_app.ps1                 # Script khởi động hệ thống (PowerShell)
```

## 🚀 Hướng dẫn cài đặt & chạy

### Yêu cầu
- Python 3.9+
- Node.js 18+
- Model weights (đã train) trong thư mục `models/`

### Cài đặt

```bash
# 1. Clone repo
git clone https://github.com/TrungNGD195/Shopping_Support_System.git
cd Shopping_Support_System

# 2. Cài đặt thư viện Python
pip install -r requirements.txt

# 3. Cài đặt thư viện Frontend
cd src/frontend && npm install && cd ../..
```

### Chạy hệ thống

**Cách 1: Chạy tự động (PowerShell)**
```powershell
.\run_app.ps1
```

**Cách 2: Chạy thủ công**
```bash
# Terminal 1 - Backend (API)
cd src && python api_server.py

# Terminal 2 - Frontend (React)
cd src/frontend && npm run dev
```

Sau khi khởi động:
- 🌐 **Web App:** http://localhost:5173
- 📡 **API Docs:** http://localhost:8000/docs

### Huấn luyện model (Tùy chọn)

Sử dụng Google Colab để huấn luyện nhanh trên GPU:
1. Upload file `colab_train_absa.ipynb` lên [Google Colab](https://colab.research.google.com)
2. Chọn Runtime → GPU (T4)
3. Upload 2 file CSV từ thư mục `data/`
4. Chạy tất cả các ô → Tải `trained_models.zip` về
5. Giải nén vào thư mục `models/`

Hoặc train trên máy local:
```bash
python src/train_absa.py --aspect Quality --batch 2
python src/train_absa.py --aspect Price --batch 2
python src/train_absa.py --aspect Delivery --batch 2
python src/train_absa.py --aspect Service --batch 2
```

## 📊 Hệ thống nhãn ABSA

| Giá trị | Ý nghĩa | Mô tả |
|---------|---------|-------|
| `-1` | Không nhắc tới | Bình luận không đề cập khía cạnh này |
| `0` | Tiêu cực (Chê) | Khách hàng phàn nàn, không hài lòng |
| `1` | Trung lập | Nhận xét bình thường, không rõ xu hướng |
| `2` | Tích cực (Khen) | Khách hàng hài lòng, khen ngợi |