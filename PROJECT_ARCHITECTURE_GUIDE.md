# TÀI LIỆU KIẾN TRÚC VÀ TỔ CHỨC MÃ NGUỒN (PROJECT ARCHITECTURE GUIDE)

Tài liệu này cung cấp cái nhìn tổng quan về kiến trúc phần mềm, cấu trúc thư mục, chức năng của từng tập tin và luồng xử lý dữ liệu của hệ thống "Shopping Support System". Tài liệu phục vụ mục đích tài liệu hóa dự án (documentation) và hỗ trợ công tác bàn giao, phát triển giữa các nhóm Frontend, Backend và Data Science.

---

## 1. TỔNG QUAN THƯ MỤC GỐC (ROOT DIRECTORY)
Dự án được phân chia thành các cấu phần độc lập nhằm đảm bảo tính toàn vẹn và dễ dàng bảo trì. Các tập tin cấu hình ở thư mục gốc bao gồm:

- `run_app.ps1`: Kịch bản (Script) PowerShell tự động hóa quá trình khởi chạy môi trường, kích hoạt Backend API (cổng 8000) và Frontend Web Server (cổng 5173).
- `requirements.txt`: Danh sách các thư viện phụ thuộc của Python (ví dụ: `fastapi`, `torch`, `transformers`, `google-genai`, `ddgs`). Đóng vai trò thiết yếu trong việc thiết lập môi trường Backend.
- `README.md` & `GUIDE.md`: Tài liệu đặc tả dự án, bao gồm thông tin nhóm, kiến trúc tổng quan, và hướng dẫn cài đặt/khởi chạy chi tiết.
- `LABELING_GUIDE.md`: Bộ quy chuẩn gán nhãn dữ liệu (Data Labeling Guidelines), xác định tiêu chí phân loại bình luận (Spam, Chất lượng, Giá cả, Giao hàng, Dịch vụ) phục vụ quá trình huấn luyện AI.
- `.gitignore`: Cấu hình Git nhằm bỏ qua các tập tin môi trường (`.env`), bộ nhớ tạm (`__pycache__`), thư viện Node (`node_modules`), và các tập tin dữ liệu kích thước lớn.
- `test_products.md` & `test_links/demo_links.txt`: Danh sách các đường dẫn (URL) sản phẩm thực tế dùng để phục vụ quá trình kiểm thử (Testing) và trình diễn (Demo).

---

## 2. MODULE FRONTEND
**Thư mục quản lý:** `src/frontend/`

Phân hệ Frontend được phát triển bằng ReactJS kết hợp với Vite. Chức năng chính là kết nối với Backend API, quản lý trạng thái giao diện và trực quan hóa dữ liệu (Data Visualization).

**Các tập tin cấu hình:**
- `package.json` & `package-lock.json`: Quản lý các gói phụ thuộc NPM (ví dụ: React, Recharts, TailwindCSS).
- `vite.config.js`: Cấu hình máy chủ phát triển Vite.
- `postcss.config.js` & `eslint.config.js`: Cấu hình bộ tiền xử lý CSS Tailwind và công cụ kiểm tra chất lượng mã nguồn (Linting).
- `index.html`: Điểm neo gốc của ứng dụng Single Page Application (SPA).
- `public/`: Thư mục chứa tài nguyên tĩnh như `favicon.svg`.

**Thư mục Lõi `src/frontend/src/`:**
- `main.jsx`: Điểm khởi chạy (Entry point) của React.
- `App.jsx`: Cấu hình định tuyến (Routing). Chuyển hướng người dùng giữa các trang `Home` và `Dashboard`.
- `index.css`: Lưu trữ định dạng CSS toàn cục và các biến thiết kế của Tailwind.
- `pages/Home.jsx`: Giao diện trang chủ chứa thanh tìm kiếm URL.
- **`pages/Dashboard.jsx`:** Tập tin cốt lõi xử lý logic giao diện.
   - **Xử lý Logic**: Thực hiện HTTP Request thông qua `fetch()` tới Endpoint của Backend.
   - **Xử lý Dữ liệu**: Phân rã cấu trúc JSON trả về để trích xuất thống kê và bình luận.
   - **Trực quan hóa (UI/UX)**: Hiển thị các thẻ thông tin (Cards), danh sách nhận xét tiêu biểu và biểu đồ phân phối cảm xúc bằng thư viện `Recharts`.

---

## 3. MODULE BACKEND VÀ TRÍ TUỆ NHÂN TẠO (AI)
Phân hệ này chịu trách nhiệm thu thập, tiền xử lý ngôn ngữ tự nhiên (NLP) và thực hiện các luồng suy luận bằng học máy (Machine Learning).

### 3.1. Khối Server & Data Fetching (`src/`)
- `src/api_server.py`: Tập tin khởi chạy Backend Server bằng FastAPI. 
   - Quản lý bộ nhớ: Ứng dụng cơ chế `lifespan` để khởi tạo các mô hình AI dung lượng lớn vào RAM/VRAM một lần duy nhất.
   - Xử lý API: Cung cấp endpoint `POST /api/analyze`, tích hợp logic bóc tách URL và sử dụng thư viện `ddgs` (DuckDuckGo) để truy xuất hình ảnh sản phẩm.
- `src/scraper.py`: Xử lý logic trích xuất mã sản phẩm từ URL và đối chiếu với tập dữ liệu lưu trữ (mô phỏng Database) để lấy danh sách bình luận tương ứng.
- `src/utils/`: Thư mục tiện ích chứa `text_processing.py` (chuẩn hóa văn bản) và `teencode_miner.py` (từ điển chuyển đổi ngôn ngữ mạng).

### 3.2. Khối AI Pipeline (`ai_core/`)
- `ai_core/inference.py`: Định nghĩa các lớp `ABSAPredictor` và `SpamPredictor`. Tương tác với PyTorch và HuggingFace Transformers để đưa ra dự đoán phân loại nhãn và cảm xúc cho văn bản.
- `ai_core/summarizer.py`: Tích hợp mô hình ngôn ngữ lớn (LLM). Cài đặt cơ chế Fallback giữa Gemini API (ưu tiên) và Gemma 4. Sử dụng kỹ thuật Prompt Engineering để tổng hợp các bình luận tiêu biểu thành đoạn tóm tắt xúc tích.
- `ai_core/scripts/`: Thư mục chứa các kịch bản thực thi tác vụ đơn lẻ (One-off scripts) nhằm tự động hóa quy trình gán nhãn và làm sạch dữ liệu lớn bằng LLM.

### 3.3. Khối Huấn luyện Mô hình & Dữ liệu (`notebooks/`, `data/`)
- `notebooks/kaggle_train_spam.ipynb`: Môi trường Jupyter Notebook phục vụ việc huấn luyện tinh chỉnh (Fine-tuning) mô hình PhoBERT cho tác vụ nhận diện Spam (Spam Filter).
- `notebooks/colab_train_absa.ipynb`: Môi trường Jupyter Notebook phục vụ việc huấn luyện mô hình phân loại đa khía cạnh và cảm xúc (Aspect-Based Sentiment Analysis).
- `data/`: Nơi lưu trữ tập dữ liệu thô và đã qua xử lý (CSV) sử dụng cho quá trình huấn luyện và kiểm thử mô hình.

---

## 4. LUỒNG HOẠT ĐỘNG CỦA HỆ THỐNG (SYSTEM WORKFLOW)
Quy trình xử lý dữ liệu end-to-end từ khi tiếp nhận yêu cầu đến khi trả về kết quả:

1. **User Input:** Người dùng nhập URL sản phẩm thông qua giao diện tìm kiếm tại `Home.jsx`.
2. **Frontend Request:** Môi trường Frontend định tuyến URL tới Endpoint `POST /api/analyze` của Backend.
3. **Metadata Extraction:** Backend bóc tách siêu dữ liệu (Tên sản phẩm) và tự động truy xuất ảnh minh họa thông qua DuckDuckGo Search API.
4. **Data Aggregation:** Hệ thống trích xuất danh sách bình luận tương ứng với mã định danh sản phẩm.
5. **Spam Filtering:** Chuỗi bình luận được đưa qua mô hình PhoBERT Spam Filter. Các bình luận vi phạm hoặc không mang giá trị ngữ nghĩa sẽ bị loại bỏ.
6. **Sentiment Classification:** Tập dữ liệu bình luận hợp lệ được xử lý qua mô hình PhoBERT ABSA để phân loại thành các khía cạnh (Giá cả, Dịch vụ, v.v.) và gán nhãn cảm xúc (Tích cực/Tiêu cực).
7. **Generative Summarization:** Trích xuất các bình luận tiêu biểu nhất đại diện cho từng khía cạnh và chuyển tới hệ thống LLM (Gemini/Gemma) để tự động hóa việc khởi tạo nội dung tóm tắt.
8. **Frontend Rendering:** Khối lượng dữ liệu hoàn chỉnh (JSON) được phản hồi về Frontend. Giao diện cập nhật trạng thái hiển thị và trực quan hóa kết quả thành các dạng biểu đồ.

---

## 5. CẤU TRÚC NHÁNH ĐIỀU KHIỂN PHIÊN BẢN (GIT BRANCH STRATEGY)
Kho lưu trữ (Repository) áp dụng chiến lược phân tách nhánh nghiêm ngặt (Poly-repo style) nhằm cô lập các thành phần hệ thống:

- **Nhánh `main`:** Tích hợp toàn diện toàn bộ mã nguồn Frontend, Backend và mô hình Trí tuệ nhân tạo.
- **Nhánh `feature/frontend-ai`:** Cô lập hoàn toàn thư mục `src/frontend/` và các thiết lập UI/UX. Không chứa mã nguồn máy chủ hay dữ liệu huấn luyện.
- **Nhánh `backend-ai`:** Chỉ bao gồm mã nguồn API Server, cấu trúc AI Pipeline, tập lệnh huấn luyện và cơ sở dữ liệu.
- **Nhánh `crawl`:** Lưu trữ lịch sử các đoạn mã thu thập dữ liệu (Legacy Crawler, Extensions) và các tệp dữ liệu thô phục vụ mục đích báo cáo và truy vết nguồn gốc tập dữ liệu.
