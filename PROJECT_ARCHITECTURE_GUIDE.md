# CHI TIẾT KIẾN TRÚC & PHÂN BỔ MÃ NGUỒN (SHOPPING SUPPORT SYSTEM)

Tài liệu này là "bản đồ toàn cảnh" siêu chi tiết về hệ thống. Mục đích là để **Trung (làm Frontend)** và **Bạn (làm Backend/AI)** hiểu tường tận hệ thống đang có những thư mục gì, mỗi file dùng để làm gì và luồng dữ liệu chạy như thế nào.

Qua đó, hai bạn có thể san sẻ công việc, chuẩn bị báo cáo, trình bày trước hội đồng một cách tự tin nhất.

---

## PHẦN 1: TỔNG QUAN THƯ MỤC GỐC (ROOT FOLDERS)
Dự án được chia thành các cấu phần rõ rệt để có thể "xé nhỏ" ra làm các nhánh (branch) riêng biệt.

### 1. Các file cấu hình nền tảng ở thư mục gốc:
- `run_app.ps1`: File kịch bản (script) PowerShell tự động hóa để chạy dự án. Chỉ cần click đúp (hoặc chạy trên terminal), nó sẽ tự động kích hoạt môi trường, khởi động Backend ở cổng 8000 và bật Frontend ở cổng 5173.
- `requirements.txt`: Chứa danh sách mọi thư viện Python bắt buộc phải cài đặt (như `fastapi`, `torch`, `transformers`, `google-genai`, `ddgs`...).
- `README.md` & `GUIDE.md`: Các tài liệu hướng dẫn nhanh về cách cài đặt, cách chạy lệnh và tổng quan dự án.
- `LABELING_GUIDE.md`: Hướng dẫn các nguyên tắc dùng để "gán nhãn" cho các bình luận (Spam là gì, Khen là gì, Chê là gì). Rất hữu ích để báo cáo quá trình chuẩn bị Dữ Liệu.
- `.gitignore`: Chặn không cho Git tải lên mạng các file rác, file nhạy cảm (`.env`), file Data lớn (`.csv`) và thư mục `node_modules/`.
- `test_products.md` & `test_links/demo_links.txt`: Danh sách các đường link sản phẩm để test thuật toán.

---

## PHẦN 2: FRONTEND (DÀNH CHO TRUNG)
**Toàn bộ nằm trong thư mục `src/frontend/`**

Thư mục này là một dự án ReactJS độc lập (tạo bằng Vite). Trách nhiệm của Trung là vẽ biểu đồ, lấy dữ liệu JSON từ Backend hiển thị ra bảng, thẻ và điều phối các trạng thái loading, lỗi (error).

- `package.json` & `package-lock.json`: Chứa danh sách các thư viện Node.js (React, Recharts để vẽ biểu đồ biểu diễn AI, TailwindCSS để làm giao diện đẹp).
- `vite.config.js`: File cấu hình lõi của Vite, giúp server Frontend chạy ở cổng 5173.
- `postcss.config.js` & `eslint.config.js`: Cấu hình hỗ trợ đọc mã CSS của Tailwind và kiểm tra lỗi cú pháp (Linting).
- `index.html`: File HTML gốc duy nhất (Single Page Application). Nơi mọi đoạn mã React sẽ nhúng vào `<div id="root">`.
- `public/`: Chứa file `favicon.svg` (icon góc trình duyệt) và các ảnh/icon tĩnh.

**Thư mục Lõi `src/frontend/src/`:**
- `main.jsx`: File gốc rễ khởi chạy React.
- `App.jsx`: Bộ định tuyến (Router). Khai báo đường dẫn `/` thì mở trang `Home`, `/dashboard` thì mở trang `Dashboard`.
- `index.css`: Toàn bộ các biến màu CSS (Xanh, Trắng, Đỏ) và phong cách chung của Tailwind.
- `pages/Home.jsx`: Mã nguồn trang chủ. Chỉ có ô Search bar và ảnh background. Khi người dùng bấm Tìm Kiếm, nó sẽ đẩy người dùng sang trang `Dashboard.jsx`.
- **`pages/Dashboard.jsx` (QUAN TRỌNG NHẤT):**
   - **Xử lý Logic**: Dùng `fetch()` gọi tới `http://localhost:8000/api/analyze` để lấy kết quả từ Backend.
   - **Cấu trúc Dữ liệu**: Xử lý JSON trả về (gồm 4 mảng aspect, số lượng bình luận, tên/ảnh sản phẩm).
   - **Giao diện (UI)**: Chứa các hàm `renderOverview()` vẽ 4 thẻ khía cạnh, `renderAspectDetail()` vẽ 2 cột Nhận Xét Tiêu Biểu, tích hợp Biểu đồ tròn (Pie Chart) hiển thị tỉ lệ Khen/Chê bằng `Recharts`.

---

## PHẦN 3: BACKEND, AI VÀ DỮ LIỆU (DÀNH CHO BẠN)
Khối này là "bộ não" thực sự của dự án, bao gồm xử lý API, xử lý văn bản, phân loại bằng Trí Tuệ Nhân Tạo.

### 1. Khối Server & Crawler (`src/`)
- `src/api_server.py`: Trái tim Backend (FastAPI). 
   - Nó mở cổng mạng `8000`.
   - Có cơ chế `lifespan` cực hay: Load 2 mô hình AI nặng hàng GB vào bộ nhớ (RAM/VRAM) **chỉ 1 lần duy nhất** khi khởi động Server để tránh sập máy.
   - Có API `/api/analyze`. Trong API này có logic tự động tách chuỗi URL, dùng thư viện `ddgs` (DuckDuckGo) ép từ khóa `"shopee"` để cào được đúng ảnh sản phẩm để gửi cho Frontend.
- `src/scraper.py`: Nhận link, tách ID sản phẩm và đối chiếu với database CSV nội bộ để bốc ra hàng trăm comments tương ứng mô phỏng hoạt động thực tế.
- `src/utils/`: Thư mục con chứa `text_processing.py` (làm sạch dấu câu, viết tắt) và `teencode_miner.py` (dịch các từ teencode Việt Nam về chuẩn).

### 2. Khối AI Pipeline (`ai_core/`)
- `ai_core/inference.py`: Chứa class `ABSAPredictor` và `SpamPredictor`. Nơi giao tiếp trực tiếp với bộ thư viện PyTorch và Transformers để phán đoán 1 bình luận là Spam hay Hợp Lệ, và thuộc loại Khen/Chê nào.
- `ai_core/summarizer.py`: Nơi thực hiện **Prompt Engineering**. Hệ thống này dùng cơ chế kết nối API LLM song song: Ưu tiên dùng `Gemini` do nhanh và cấu trúc JSON chuẩn. Nếu Gemini lỗi (hoặc nhập API Key ảo), nó tự động "Fallback" sang `Gemma 4`. Nó sẽ lấy các bình luận tiêu biểu từ PhoBERT đưa cho LLM tổng hợp lại thành câu văn tự nhiên.
- `ai_core/scripts/`: Chứa vô vàn các script chạy 1 lần (`auto_label_spam_gemini.py`, `auto_label_absa_gemma.py`, `process_shopee_data.py`...) dùng để nhờ LLM gán nhãn tự động cho hàng vạn dòng dữ liệu thô.

### 3. Khối Huấn luyện Mô hình & Data (`notebooks/`, `data/`)
- `notebooks/kaggle_train_spam.ipynb`: File Jupyter dùng trên máy chủ Kaggle (có GPU). Chứa mã nguồn đọc file CSV, filter dữ liệu rác, nạp pretrained `vinai/phobert-base-v2` và tiến hành Huấn Luyện (Finetuning) mô hình Spam Filter.
- `notebooks/colab_train_absa.ipynb`: Tương tự như trên nhưng dùng để train mô hình phân loại cảm xúc (ABSA - Aspect Based Sentiment Analysis) dựa trên dữ liệu 4 nhãn.
- `data/`: Chứa các bộ dữ liệu CSV khổng lồ (`positive_reviews.csv`, `negative_reviews.csv`, `dataset_split/`) làm thức ăn cho các file `.ipynb` phía trên.

---

## PHẦN 4: LUỒNG HOẠT ĐỘNG CHI TIẾT (WORKFLOW 8 BƯỚC)
Đây là quy trình cực chuẩn để hai bạn báo cáo hoặc vẽ Sơ đồ luồng dữ liệu (Sequence Diagram):

1. **User Input:** Người dùng nhập URL Tiki/Shopee vào ô tìm kiếm của `Home.jsx` và bấm tìm.
2. **Frontend Request:** React gửi mã URL đó qua cổng mạng tới Endpoint `POST /api/analyze` của `api_server.py`.
3. **Product Metadata:** Backend nhận URL, chọc qua hàm `get_product_info()` lấy tên sản phẩm và gọi DuckDuckGo Image AI để lấy ra Ảnh thu nhỏ.
4. **Data Fetching:** Gọi module `scraper.py`, đối chiếu ID trong URL để móc hàng loạt bình luận trong Data Lake CSV ra ngoài.
5. **Spam Filtering (PhoBERT):** Lùa toàn bộ bình luận qua mô hình Spam. Bất cứ câu nào có nhãn 0 (quảng cáo, rác, chéo xu) lập tức bị loại bỏ khỏi luồng.
6. **Sentiment Analysis (PhoBERT ABSA):** Các bình luận sạch còn lại được đưa qua mô hình ABSA. Từng câu được dán nhãn thuộc khía cạnh nào (Giá, Dịch vụ...) và mang cảm xúc gì (Khen/Chê).
7. **Generative Summarization (Gemini/Gemma):** Chọn 5 bình luận Khen và 5 bình luận Chê hay nhất, gom chung ném cho LLM qua `summarizer.py` yêu cầu AI đọc và viết một đoạn tóm tắt sắc bén ngắn gọn.
8. **Frontend Rendering:** FastAPI gom tất cả (Thông tin, Thống kê, Nhận xét tiêu biểu, Lời Tóm tắt) thành JSON trả về Frontend. React lập tức tắt Loading, kích hoạt hiệu ứng hoạt hình và vẽ lên biểu đồ đầy màu sắc rực rỡ.

---

## PHẦN 5: KIỂM TRA TRẠNG THÁI GIT (NHÁNH)
Tôi đã kiểm tra và tiến hành **Push hoàn chỉnh 100%** lên các nhánh Git của bạn theo đúng nguyên tắc "Poly-repo" sạch sẽ, tuyệt đối không bị trộn lẫn:

- **Nhánh `main`**: Đầy đủ Full-stack. Là bản tổng hợp hoàn hảo nhất.
- **Nhánh `feature/frontend-ai`**: Chỉ có duy nhất folder Frontend và các file cấu hình giao diện. Hoàn toàn sạch bóng code Backend hay AI.
- **Nhánh `backend-ai`**: Tập trung toàn lực vào `ai_core`, `notebooks`, `src/api_server.py` và `data`. Đã xóa triệt để Frontend.
- **Nhánh `crawl`**: Lưu trữ source Crawler cũ, Extension trình duyệt Javascript, và file Dữ liệu thô dùng làm bằng chứng để bảo vệ hội đồng rành rọt.

Tất cả đã đồng bộ chặt chẽ trên Github. Hai bạn có thể tải về và sử dụng ngay lập tức!
