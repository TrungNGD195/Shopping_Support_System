# Project SSS

# PHẦN 1: TỔNG QUAN DỰ ÁN (PROJECT OVERVIEW)

## 1. Tên dự án:
**Shopping Support System (Hệ thống hỗ trợ mua sắm thông minh)**

## 2. Mục tiêu dự án:
Xây dựng một hệ thống hỗ trợ ra quyết định mua hàng bằng cách tự động thu thập, phân tích và tóm tắt bình luận từ các sàn thương mại điện tử (Shopee, Lazada, Tiki...). Hệ thống giúp người dùng tiết kiệm thời gian đọc hàng trăm comment bằng cách cung cấp bảng tóm tắt ưu/nhược điểm theo tiêu chí cụ thể.

## 3. Luồng xử lý nghiệp vụ (Business Flow):

- **Bước 1: Tiếp nhận Input (Đầu vào)**
    - Người dùng cung cấp đường dẫn (Link/URL) trực tiếp của một sản phẩm trên các sàn TMĐT (Shopee, Lazada, Tiki...) vào hệ thống.
- **Bước 2: Thu thập dữ liệu (Crawling)**
    - Truy cập vào đường link sản phẩm đã nhận ở Bước 1.
    - Tự động lấy các thông tin: Tên sản phẩm, Giá, Mô tả sản phẩm, Hình ảnh chính, Toàn bộ bình luận/đánh giá (reviews) của người mua.
- **Bước 3: Tiền xử lý dữ liệu (Preprocessing)**
    - Loại bỏ các comment rác, spam, icon vô nghĩa.
    - Xử lý các ngôn ngữ teen code, viết tắt, sai chính tả (nếu cần).
    - Phân loại comment theo tiêu chí (Chất lượng, Đóng gói, Giao hàng, Thái độ phục vụ...).
- **Bước 4: Phân tích & Tóm tắt (Analysis & Summarization)**
    - Sử dụng AI (LLM) để phân tích sắc thái (Sentiment Analysis): Tích cực, Tiêu cực, Trung lập cho từng khía cạnh.
    - Rút trích các điểm chính: Ưu điểm nổi bật và Nhược điểm cần lưu ý.
- **Bước 5: Tóm tắt (Summary Generator)**
    - Hệ thống tự động tạo ra một đoạn tóm tắt ngắn gọn (khoảng 3-5 câu) tổng quan về sản phẩm dựa trên hàng trăm reviews.
- **Bước 6: Hiển thị (Display/UI)**
    - Trả về giao diện cho người dùng bảng tóm tắt so sánh trực quan, điểm số trung bình cho từng tiêu chí.

---

# PHẦN 2: PHÂN CHIA CÔNG VIỆC

## Giai đoạn 1: Chuẩn bị & Thu thập dữ liệu

| Tên công việc | Chi tiết công việc | Kết quả đầu ra | Phụ trách | Deadline | Status | URL |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Setup Project & Git** | - Tạo repo Github. Cấu trúc folder: `/backend`, `/frontend`, `/data`, `/models`.<br>- Tạo `virtualenv`.<br>- Cài thư viện: `pandas`, `selenium`, `torch`, `transformers`, `streamlit`. | Link Github đã init cấu trúc. | Khánh, Trung | February 10, 2026 | **Done** | [Link Git](https://github.com/TrungNGD195/Shopping_Support_System.git) |
| **Crawler cơ bản** | - Dùng Selenium hoặc Playwright giả lập trình duyệt.<br>- Logic: Truy cập link -> Scroll xuống cuối để load comment -> Click nút "Next page" -> Lặp lại.<br>- Lấy các trường: `author`, `rating`, `comment`, `time`. | Script `crawler.py` chạy ổn định, không bị crash khi mạng lag. | Khánh | February 16, 2026 | **Done** | |
| **Thu thập Data** | - Thu thập 10,000 comments từ các shop mỹ phẩm, đồ điện tử trên Shopee.<br>- Lưu file `raw_reviews.csv`. | File CSV chứa 10k dòng dữ liệu. | Khánh | February 20, 2026 | **Done** | |

## Giai đoạn 2: Xây dựng AI Core

| Tên công việc | Chi tiết công việc | Kết quả đầu ra | Phụ trách | Deadline | Status | URL |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train Model ABSA (Quality & Price)** | - Label dữ liệu (Tích cực/Tiêu cực) cho 2 khía cạnh: Chất lượng, Giá cả.<br>- Finetune PhoBERT. | Model file `.bin` đạt Accuracy > 85% trên tập test. | Trung | March 15, 2026 | **Done** | |
| **Train Model ABSA (Delivery & Service)** | - Label dữ liệu cho 2 khía cạnh: Giao hàng, Dịch vụ.<br>- Finetune PhoBERT. | Model file `.bin` đạt Accuracy > 82% trên tập test. | Trung | March 20, 2026 | **Done** | |

## Giai đoạn 3: Tóm tắt & Tích hợp Logic

| Tên công việc | Chi tiết công việc | Kết quả đầu ra | Phụ trách | Deadline | Status | URL |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tóm tắt (Summary)** | - Dùng GPT-3.5 hoặc VinAI-BART để tóm tắt các comment tiêu biểu của từng khía cạnh.<br>- Ghép các ý thành đoạn văn hoàn chỉnh. | Script `summarizer.py` nhận vào list comment -> Trả về 1 đoạn tóm tắt. | Khánh | April 1, 2026 | **Done** | |

## Giai đoạn 4: Web Frontend

| Tên công việc | Chi tiết công việc | Kết quả đầu ra | Phụ trách | Deadline | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Thiết kế luồng đa trang (Multi-page)** | Trang chủ (nhập Link) tinh gọn ở giữa. Trang Dashboard trải rộng, chia 4 Tabs (Chất lượng, Giá cả, Giao hàng, Dịch vụ) | | Trung | April 4, 2026 | **Done** |
| **Code Home** | Dùng `st.set_page_config(layout="centered")`. Dùng `st.text_input` nhận Link. Dùng `st.session_state` để lưu trữ Link chuyển sang trang sau. | File `app.py` nhận link và có nút chuyển trang | Trung | April 4, 2026 | **Done** |
| **Code Result** | Dùng `st.set_page_config(layout="wide")`. Kết hợp `st.tabs` và `st.columns(2)` để layout. Vẽ biểu đồ donut bằng `plotly.express`. Dùng `st.expander` để giấu/hiện comment bằng chứng. | File `1_phan_tich.py` hiển thị mượt màng với Mock Data | Trung | April 7, 2026 | **Done** |
| **Integration (Ghép nối AI)** | Import trực tiếp file `src/inference.py` vào `1_phan_tich.py`. Dùng `st.spinner()` làm hiệu ứng chờ khi AI nạp model và chấm điểm dữ liệu. | Dashboard hiển thị số liệu thật từ kết quả dự đoán của PhoBERT | Trung | April 8, 2026 | **Done** |
