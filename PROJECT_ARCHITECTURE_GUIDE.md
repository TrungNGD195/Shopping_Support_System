# HƯỚNG DẪN KIẾN TRÚC & QUY TRÌNH HỆ THỐNG (PROJECT ARCHITECTURE GUIDE)

Tài liệu này được thiết kế để giúp nhóm (bạn và Trung) hiểu rõ tường tận từng ngóc ngách của dự án "Shopping Support System". Qua đó, hai bạn có thể chia lại khối lượng công việc (Workload) một cách công bằng và phối hợp nhịp nhàng hơn.

---

## PHẦN 1: TỔNG QUAN LUỒNG HOẠT ĐỘNG (SYSTEM WORKFLOW)
Hệ thống hoạt động theo mô hình **Client-Server** kết hợp **AI Pipeline**. Khi người dùng dán 1 link sản phẩm vào web, luồng dữ liệu chạy như sau:

1. **[FRONTEND]**: Người dùng dán URL (Tiki/Shopee) vào thanh tìm kiếm trên Web và bấm "Phân tích".
2. **[FRONTEND -> BACKEND]**: React gửi 1 request `POST /api/analyze` chứa URL đó xuống cho Server FastAPI.
3. **[BACKEND]**: FastAPI tiếp nhận URL, dùng hàm `get_product_info()` để chọc vào API của Tiki/Shopee lấy Tên và dùng DuckDuckGo AI để kiếm Ảnh sản phẩm.
4. **[BACKEND (CRAWLER)]**: FastAPI gọi module `scraper.py`. Module này sẽ quét mã ID của sản phẩm và bốc ra hàng trăm bình luận tương ứng (hiện tại đang đọc từ file CSV local mô phỏng Database).
5. **[BACKEND (AI PIPELINE)]**: 
   - Đưa hàng trăm bình luận qua **Mô hình AI 1 (PhoBERT Spam Filter)**: Lọc vứt đi các bình luận rác, câu like, quảng cáo.
   - Đưa các bình luận sạch qua **Mô hình AI 2 (PhoBERT ABSA)**: Phân loại từng bình luận vào 4 khía cạnh (Chất lượng, Giá cả, Giao hàng, Dịch vụ) và dán nhãn cảm xúc (Khen/Chê/Bình thường).
6. **[BACKEND (LLM)]**: FastAPI nhặt ra các bình luận Khen/Chê tiêu biểu nhất, gói lại gửi cho **Gemini (hoặc Gemma)** để nhờ AI này viết một đoạn "Tổng quan tóm tắt" ngắn gọn, sâu sắc.
7. **[BACKEND -> FRONTEND]**: Đóng gói toàn bộ số liệu thống kê, bình luận tiêu biểu, ảnh sản phẩm, và lời tóm tắt thành 1 cục JSON gửi trả lại cho Web.
8. **[FRONTEND]**: React nhận cục JSON, vẽ lên các biểu đồ tròn, render danh sách bình luận và hiển thị giao diện kết quả cực đẹp mắt.

---

## PHẦN 2: CHI TIẾT FRONTEND (Dành cho Trung)
**Trách nhiệm của Trung**: Xử lý toàn bộ logic giao diện, trải nghiệm người dùng (UX), biểu diễn dữ liệu (Data Visualization), và kết nối API.

📂 **Thư mục quản lý**: `src/frontend/`
- Đây là một dự án React thuần túy được build bằng công cụ **Vite** để cho tốc độ siêu nhanh.

**Các file/thư mục quan trọng**:
- 📄 `package.json`: Chứa danh sách các thư viện FE đang dùng (React, Recharts để vẽ biểu đồ, TailwindCSS để style, Phosphor-icons để lấy icon).
- 📄 `postcss.config.js` & `index.css`: Nơi cấu hình TailwindCSS. Mọi biến màu sắc (Đỏ, Xanh, Vàng) và các class tiện ích đều được khai báo ở đây.
- 📂 `src/App.jsx` & `main.jsx`: File gốc (Entry point) của React. Nó khởi tạo ứng dụng và điều hướng (Routing).
- 📂 `src/pages/Home.jsx`: Giao diện trang chủ ban đầu (nơi có cái background đẹp và ô nhập URL).
- 📂 `src/pages/Dashboard.jsx`: **Đây là "trái tim" của Frontend**. 
   - File này dài nhất, chứa logic `fetch()` gọi xuống Backend.
   - Nó chứa các hàm `renderOverview()`, `renderAspectDetail()` để hứng dữ liệu JSON và vẽ ra các Thẻ thống kê (Cards), Thanh trạng thái, Biểu đồ (Recharts), và cột chứa Ảnh + Tên sản phẩm.

🎯 **Gợi ý học tập cho Trung**:
1. Đọc hiểu file `Dashboard.jsx` trước để xem cách React gọi API bằng hàm `handleAnalyze`.
2. Học cách sử dụng thư viện **Recharts** để tùy biến màu sắc biểu đồ.
3. Học cách quản lý State (`useState`, `useEffect`) để làm loading spinner (hiệu ứng xoay xoay lúc chờ AI phân tích).

---

## PHẦN 3: CHI TIẾT BACKEND & AI (Dành cho Bạn)
**Trách nhiệm của Bạn**: Đây là phần lõi cực kỳ nặng đô. Bạn phụ trách xử lý Dữ liệu, huấn luyện AI, làm API Server và kỹ thuật Prompt Engineering.

📂 **Thư mục quản lý**: `src/` (Trừ frontend), `ai_core/`, `models/`, `notebooks/`, `data/`.

**1. Khối Server API (`src/`)**:
- 📄 `api_server.py`: Trái tim của Backend (viết bằng FastAPI). Nhiệm vụ của nó là mở cổng mạng (Port 8000), định nghĩa API `/api/analyze`, lấy ảnh bằng DuckDuckGo, và gọi các logic AI.
- 📄 `scraper.py`: File chịu trách nhiệm bóc tách ID sản phẩm từ URL và đi "lấy" bình luận (mockup từ file Excel/CSV). Trong thực tế nó là cầu nối tới Database.

**2. Khối AI Pipeline (`ai_core/`)**:
- 📄 `inference.py`: Chứa class `ABSAPredictor` và `SpamPredictor`. Nó load các file trọng số (weights) của AI vào RAM/VRAM và có hàm `predict()` để chạy phán đoán cho từng câu.
- 📄 `summarizer.py`: Khối giao tiếp với LLM siêu lớn (Gemini API hoặc Gemma 4). Chứa kỹ thuật viết Prompt (Prompt Engineering) để ép con AI phải tóm tắt theo đúng ý đồ của mình mà không bịa chuyện.
- 📂 `scripts/`: Chứa các script Python chạy tay (one-off) để tự động hóa việc gán nhãn dữ liệu bằng Gemma.

**3. Khối Huấn Luyện AI (`notebooks/` & `models/`)**:
- 📂 `notebooks/kaggle_train_spam.ipynb`: Code chạy trên máy chủ Kaggle/Colab dùng card GPU xịn để dạy cho mô hình PhoBERT biết thế nào là Spam.
- 📂 `notebooks/colab_train_absa.ipynb`: Code dạy mô hình PhoBERT phân loại 4 khía cạnh và cảm xúc (ABSA).
- 📂 `models/`: Nơi chứa kết quả sau khi train (các file `pytorch_model.bin` nặng hàng trăm MB).

🎯 **Gợi ý học tập cho Bạn**:
1. Đọc hiểu `api_server.py` để biết FastAPI khởi tạo (Lifespan) và load model AI vào RAM 1 lần duy nhất như thế nào để tránh tràn RAM.
2. Hiểu thư viện `transformers` và `torch` trong file `inference.py`.
3. Tập tinh chỉnh (Tuning) câu lệnh Prompt trong `summarizer.py` để LLM trả lời hay hơn.

---

## PHẦN 4: CHI TIẾT CRAWLER (Quá khứ & Data Collection)
Phần này hiện tại **đã hoàn thành** và chỉ dùng để lưu trữ báo cáo/thuyết trình.

📂 **Thư mục quản lý**: `legacy_extension/`, `archive_raw_data/`, `charted_sea_scraper/`.
- 📂 `legacy_extension/`: Chứa source code của một Chrome Extension bằng Javascript. Trước kia team dùng nó để cài vào trình duyệt, bấm nút là nó tự động lướt trang Shopee/Tiki và copy bình luận tải về máy.
- 📂 `charted_sea_scraper/`: Tool cào dữ liệu xịn hơn (có thể mua hoặc dùng API) để vượt qua lớp chống bot của nền tảng.
- 📂 `archive_raw_data/`: Bằng chứng "phạm tội" – chứa tất cả các file JSON, CSV thô ráp cào được từ web trước khi mang đi gán nhãn và làm sạch.

---

## GỢI Ý CHIA LẠI CÔNG VIỆC CHO CÂN BẰNG
Đúng là khối lượng Backend/AI hiện tại đang gấp 3 lần Frontend. Để cân bằng, bạn có thể đẩy bớt một số task cho Trung:

1. **Giao Frontend làm Mockup Data**: Trung có thể tự viết code React để tự giả lập một cục JSON mồi (như cấu trúc JSON Backend trả về) để bạn ấy tự code UI mà không cần đợi Backend chạy xong hay bật Model AI lên.
2. **Trung phụ trách làm Báo Cáo / Slide**: Vì Frontend có tư duy thẩm mỹ, hãy giao cho Trung việc chụp ảnh ứng dụng, vẽ sơ đồ luồng dữ liệu (Workflow) ra Figma hoặc PowerPoint.
3. **Mở rộng tính năng UI**: Bảo Trung làm thêm chức năng "Dark Mode", "Export PDF kết quả", hoặc hiển thị biểu đồ theo thời gian thực (Skeleton Loading) để tăng điểm cộng cho Frontend.
4. **Bạn (Backend) tập trung vào Scale**: Tối ưu hóa API nhanh hơn, thiết kế Database thực sự (MySQL/MongoDB) thay vì đọc từ CSV, và chuẩn bị tài liệu về kiến trúc Model AI để trả lời phản biện với giảng viên.
