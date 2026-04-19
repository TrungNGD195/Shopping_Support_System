# 🛒 Shopping Support System

Hệ thống hỗ trợ mua sắm thông minh, giúp tự động thu thập và phân tích cảm xúc (Khen/Chê) từ hàng ngàn bình luận của khách hàng trên các sàn TMĐT (Shopee, Lazada, Tiki). Từ đó, cung cấp cho người dùng bảng Dashboard tổng quan nhất trước khi quyết định mua hàng.

## 👥 Thành viên nhóm
* **Nguyễn Gia Đức Trung - B23DCVT423:** AI Core (PhoBERT), Text Preprocessing & Frontend (Streamlit)
* **Bế Quốc Khánh - B23DCCE049:** Data Crawler (Selenium), Data Aggregation & Backend Logic

## 🛠 Công nghệ sử dụng
* **Ngôn ngữ:** Python 3.9+
* **AI/NLP Framework:** Transformers (HuggingFace), PyTorch, PhoBERT
* **Tiền xử lý Text:** Underthesea (Word Segmentation), Regex
* **Crawler:** Selenium / Playwright
* **Giao diện & Web App:** Streamlit, Plotly (Vẽ biểu đồ)

## ⚙️ Luồng hoạt động của hệ thống (Pipeline)
1. **Input:** Người dùng dán Link sản phẩm vào giao diện Streamlit.
2. **Crawling:** Hệ thống tự động cào ~100-200 bình luận mới nhất.
3. **Preprocessing:** Làm sạch văn bản, chuẩn hóa tiếng Việt, dịch teencode.
4. **AI Inference:** Đưa dữ liệu qua 4 mô hình PhoBERT để gán nhãn cảm xúc cho 4 khía cạnh: *Chất lượng, Giá cả, Giao hàng, Dịch vụ*.
5. **Output:** Hiển thị thống kê % và tóm tắt ưu/nhược điểm lên Dashboard trực quan.

## 📂 Cấu trúc dự án
```text
📦 Shopping_Support_System
 ┣ 📂 models/        # Chứa nơi lưu trữ hoặc model weights sau huấn luyện
 ┣ 📂 notebooks/     # Môi trường chạy thử nghiệm thuật toán (Jupyter)
 ┣ 📂 src/           # Mã nguồn chính của dự án hiện có
 ┃ ┣ 📂 utils/       # Các module hỗ trợ xử lý ngôn ngữ
 ┃ ┃ ┣ 📜 teencode_miner.py   # Chứa class và hàm chuẩn hóa Teencode
 ┃ ┃ ┗ 📜 text_processing.py  # Chứa hàm tiền xử lý (clean_text, etc)
 ┃ ┗ 📜 train_absa.py         # Script dùng để huấn luyện mô hình ABSA (PhoBERT)
 ┣ 📜 .gitignore     # Cấu hình chặn file / models đẩy lên Git
 ┣ 📜 dummy_test.csv # Dữ liệu thử nghiệm hoặc csv test ảo
 ┣ 📜 LABELING_GUIDE.md # Chuẩn quy tắc gán nhãn dữ liệu (-1, 0, 1, 2)
 ┣ 📜 README.md      # Tài liệu giới thiệu dự án
 ┗ 📜 requirements.txt  # Danh sách thư viện cần thiết
```