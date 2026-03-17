# 🛒 Shopping Support System

Hệ thống hỗ trợ mua sắm thông minh, giúp tự động thu thập và phân tích cảm xúc (Khen/Chê) từ hàng ngàn bình luận của khách hàng trên các sàn TMĐT (Shopee, Lazada,...). Từ đó, cung cấp cho người dùng cái nhìn tổng quan nhất trước khi quyết định mua hàng.

## 👥 Thành viên nhóm
* **Nguyễn Gia Đức Trung - B23DCVT423:** AI Text Processing (PhoBERT) & Frontend (Streamlit)
* **Bế Quốc Khánh - B23DCCE049:** Data Crawler (Selenium) & Backend Integration

## 🛠 Công nghệ sử dụng
* **Ngôn ngữ:** Python 3.9+
* **AI/NLP:** PhoBERT, PyTorch, Underthesea (Word Segmentation)
* **Crawler:** Selenium
* **Giao diện (UI):** Streamlit
* **Xử lý dữ liệu:** Pandas, Regex

## 📂 Cấu trúc dự án
```text
📦 Shopping_Support_System
 ┣ 📂 data/          # Chứa dữ liệu thô cào về và dữ liệu đã làm sạch (.csv)
 ┣ 📂 models/        # Chứa file trọng số mô hình AI đã huấn luyện (.pth)
 ┣ 📂 notebooks/     # Môi trường chạy thử nghiệm thuật toán (Jupyter)
 ┣ 📂 src/           # Mã nguồn chính của dự án
 ┃ ┣ 📂 crawler/     # Script tự động cào bình luận từ web
 ┃ ┣ 📂 ui/          # Giao diện người dùng (Streamlit)
 ┃ ┗ 📂 utils/       # Các hàm hỗ trợ (làm sạch văn bản, xử lý teencode...)
 ┣ 📜 .gitignore     # Cấu hình ẩn file không cần đẩy lên Git
 ┣ 📜 LABELING_GUIDE.md # Chuẩn quy tắc gán nhãn dữ liệu cho 4 khía cạnh
 ┣ 📜 README.md      # Tài liệu hướng dẫn dự án
 ┗ 📜 requirements.txt  # Danh sách thư viện cần cài đặt