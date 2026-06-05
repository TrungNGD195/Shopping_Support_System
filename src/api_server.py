from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import uvicorn
from contextlib import asynccontextmanager

# Đảm bảo có thể import module từ ai_core và src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from ai_core.inference import ABSAPredictor, SpamPredictor
from ai_core.summarizer import ReviewSummarizer
from src.scraper import get_reviews_from_url

# Import Gemini summarizer (optional — only used if API key is configured)
summarizer = None
try:
    _ai_core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai_core")
    if _ai_core_path not in sys.path:
        sys.path.append(_ai_core_path)
    from summarizer import ReviewSummarizer
except ImportError:
    ReviewSummarizer = None

# Khởi tạo mô hình AI (Load 1 lần duy nhất khi server start)
ai_station = None
spam_station = None
summarizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_station, spam_station, summarizer
    print("[INFO] Dang nap mo hinh AI vao RAM...")
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'phobert-absa-final')
    spam_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'phobert_spam')
    
    ai_station = ABSAPredictor(model_dir)
    if os.path.exists(spam_dir):
        spam_station = SpamPredictor(spam_dir)
    else:
        print("[WARNING] Khong tim thay mo hinh Spam Filter!")
        
    # LƯU Ý: Khởi tạo với API Key của bạn (có thể để trong biến môi trường)
    api_key = "AIzaSyBjaku1UOU39XLS2IhIJolUSEtCcfFGYo8"
    summarizer = ReviewSummarizer(api_key=api_key)
    print("[INFO] Da nap thanh cong mo hinh AI va Gemini Summarizer!")
    yield
    ai_station = None
    spam_station = None
    summarizer = None

app = FastAPI(title="Shopping Support System API", lifespan=lifespan)

# Cấu hình CORS để cho phép React Web App gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str

@app.post("/api/analyze")
def analyze_product(request: AnalyzeRequest):
    url = request.url
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # 1. Lấy dữ liệu bình luận (từ Scraper giả lập)
    comments = get_reviews_from_url(url)
    
    if not comments:
        raise HTTPException(status_code=404, detail="Không tìm thấy bình luận nào cho sản phẩm này.")

    # Trích xuất thông tin sản phẩm từ URL (Tên và Ảnh)
    def get_product_info(product_url: str):
        import requests, re, urllib.parse
        info = {
            "name": "Sản phẩm Demo",
            "image": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?q=80&w=1000&auto=format&fit=crop" # Box/Shopping image fallback
        }
        try:
            if "tiki.vn" in product_url:
                match = re.search(r'-p(\d+)\.html', product_url)
                if match:
                    res = requests.get(f"https://tiki.vn/api/v2/products/{match.group(1)}", headers={"User-Agent": "Mozilla/5.0"}).json()
                    info["name"] = res.get("name", info["name"])
                    info["image"] = res.get("thumbnail_url", info["image"])
            elif "shopee.vn" in product_url:
                decoded = urllib.parse.unquote(product_url)
                match = re.search(r'shopee\.vn/(.*?)-i\.', decoded)
                if match:
                    name = match.group(1).replace('-', ' ')
                    info["name"] = name
                    # Rút gọn tên sản phẩm để tìm ảnh chính xác hơn (khoảng 8 từ đầu tiên)
                    search_name = " ".join(name.split(" ")[:8])
                    
                    # Dùng AI Search (DuckDuckGo) để tìm đúng ảnh sản phẩm đó trên mạng
                    try:
                        from duckduckgo_search import DDGS
                        with DDGS() as ddgs:
                            results = list(ddgs.images(search_name, max_results=1))
                            if results:
                                info["image"] = results[0]['image']
                    except Exception as e:
                        print(f"Lỗi tìm ảnh: {e}")
        except Exception:
            pass
        return info

    result_data = {
        "product_info": get_product_info(url),
        "overview": {
            "total_analyzed_comments": len(comments), 
            "final_verdict": "Đang tính toán...",
            "total_khen": 0,
            "total_che": 0
        },
        "aspects": {
            "Quality": {
                "name": "Chất lượng", "icon": "👕", 
                "stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, 
                "highlights": {"positive": [], "negative": []}, 
                "summary": "Đang chờ Gemini tổng hợp..."
            },
            "Price": {
                "name": "Giá cả", "icon": "💰", 
                "stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, 
                "highlights": {"positive": [], "negative": []}, 
                "summary": "Đang chờ Gemini tổng hợp..."
            },
            "Delivery": {
                "name": "Giao hàng", "icon": "🚚", 
                "stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, 
                "highlights": {"positive": [], "negative": []}, 
                "summary": "Đang chờ Gemini tổng hợp..."
            },
            "Service": {
                "name": "Dịch vụ", "icon": "🎧", 
                "stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, 
                "highlights": {"positive": [], "negative": []}, 
                "summary": "Đang chờ Gemini tổng hợp..."
            }
        }
    }

    # 2. Phân tích qua AI Station
    # Hàm làm đẹp bình luận tiêu biểu (Format lại cho đẹp thay vì copy nguyên si)
    def format_highlight(cmt: str) -> str:
        import re
        c = str(cmt)
        
        # Sửa lỗi chữ dính nhau (VD: "Màu sắc:oki,chất liệu:đẹp" -> "Màu sắc: oki, chất liệu: đẹp")
        # Tránh tách URL (http://) hoặc giờ/số (12:30, 10,000)
        c = re.sub(r'([:,])([^\s/0-9])', r'\1 \2', c)
        
        # Xóa khoảng trắng thừa và ký tự lặp
        c = re.sub(r'\s+', ' ', c).strip()
        c = re.sub(r'([.?!])\1+', r'\1', c)
        
        # Viết hoa chữ cái đầu và giữ nguyên toàn bộ nội dung (không cắt bớt)
        if c:
            c = c[0].upper() + c[1:]
        return c

    def is_spam(text: str) -> bool:
        # Nếu có mô hình AI Spam Filter, ưu tiên dùng AI (Lớp AI Phân Loại)
        if spam_station:
            return spam_station.is_spam(text)
            
        # Nếu không có mô hình, fallback về Lớp Lọc Heuristic (Keyword)
        text = str(text).lower()
        real_keywords = [
            "vải", "chất", "đẹp", "xấu", "rẻ", "đắt", "màu", "size", "form", "mặc", 
            "giao", "shop", "gói", "tư", "vấn", "thơm", "xịn", "ok", "tốt", "ưng", "nhanh", "chậm",
            "nồi", "máy", "thiết", "kế", "dùng", "sử", "dụng", "mua", "test", "hàng", "tiền", "giá",
            "bảo hành", "chắc", "bền", "lỗi", "hư", "hỏng", "thích", "tuyệt", "kém", "tệ",
            "áo", "quần", "ủi", "nước", "nhựa", "kim loại", "tạm", "ổn", "khen", "chê",
            "thất vọng", "hài lòng", "đáng", "phí", "xứng", "chất lượng", "vừa", "rộng", "chật",
            "ngắn", "dài", "mỏng", "dày", "cứng", "mềm", "mịn", "xù", "nóng", "mát",
            "chạy", "êm", "ồn", "giặt", "sạch", "pin", "sạc", "màn", "âm thanh", "chuẩn",
            "đóng gói", "cẩn thận", "nhẹ", "nặng", "to", "nhỏ", "bóp", "kéo", "khóa", "túi"
        ]
        real_count = sum(1 for kw in real_keywords if kw in text)
        
        if text.count('\n') >= 3 and len(text) > 80 and real_count < 2:
            return True
            
        if any(kw in text for kw in ["nhận xu", "lấy xu", "săn xu", "mang tính chất", "chống trôi"]):
            if real_count < 2 and not (len(text) > 50 and real_count >= 1): 
                return True
            
        if len(text.strip()) < 5: return True
        
        # DEMO HOTFIX: Chặn các bình luận rác cụ thể có thật trong Data
        if "park shin hye" in text or "choi tae joon" in text or "fancafe" in text:
            return True
            
        return False

    for cmt in comments:
        # Bỏ qua bình luận rác, thơ ca để không đưa vào Ý kiến tiêu biểu
        if is_spam(cmt):
            continue
            
        # Predict uses CPU so it takes time per comment
        prediction = ai_station.predict(cmt)
        
        # Aggregate statistics
        for aspect in result_data["aspects"]:
            sentiment = prediction.get(aspect)
            formatted_cmt = format_highlight(cmt)
            
            if sentiment == "Tích cực (Khen)":
                result_data["aspects"][aspect]["stats"]["Khen"] += 1
                result_data["aspects"][aspect]["highlights"]["positive"].append(formatted_cmt)
            elif sentiment == "Tiêu cực (Chê)":
                result_data["aspects"][aspect]["stats"]["Chê"] += 1
                result_data["aspects"][aspect]["highlights"]["negative"].append(formatted_cmt)
            elif sentiment == "Bình thường":
                result_data["aspects"][aspect]["stats"]["Bình thường"] += 1
            else:
                result_data["aspects"][aspect]["stats"]["Không nhắc tới"] += 1

    # 3. Tính toán Verdict tổng quan
    total_khen = sum([result_data["aspects"][asp]["stats"]["Khen"] for asp in result_data["aspects"]])
    total_che = sum([result_data["aspects"][asp]["stats"]["Chê"] for asp in result_data["aspects"]])

    if total_khen > total_che:
        verdict_html = "<span class='verdict-good'>🟢 Rất Đáng Mua</span>"
    elif total_che > total_khen:
        verdict_html = "<span class='verdict-bad'>🔴 Cần Cân Nhắc</span>"
    else:
        verdict_html = "<span class='verdict-neutral'>🟡 Phân vân (Trung lập)</span>"

    result_data["overview"]["final_verdict"] = verdict_html
    result_data["overview"]["total_khen"] = total_khen
    result_data["overview"]["total_che"] = total_che

    # 4. Yêu cầu Gemini tóm tắt và lọc bình luận cho từng khía cạnh
    for aspect in result_data["aspects"]:
        pos_list = list(dict.fromkeys(result_data["aspects"][aspect]["highlights"]["positive"]))
        neg_list = list(dict.fromkeys(result_data["aspects"][aspect]["highlights"]["negative"]))
        
        # Chỉ gửi tối đa 10 câu mỗi loại để Gemini xử lý nhanh, tránh quota
        pos_list = pos_list[:10]
        neg_list = neg_list[:10]
        
        vi_name = result_data["aspects"][aspect]["name"]
        
        if summarizer and (pos_list or neg_list):
            try:
                gemini_data = summarizer.summarize_and_extract(vi_name, pos_list, neg_list)
                result_data["aspects"][aspect]["summary"] = gemini_data.get("summary", "Không thể tóm tắt.")
                # Ghi đè lại ý kiến tiêu biểu bằng kết quả cắt tỉa của Gemini!
                if gemini_data.get("positive_highlights"):
                    result_data["aspects"][aspect]["highlights"]["positive"] = gemini_data["positive_highlights"]
                else:
                    result_data["aspects"][aspect]["highlights"]["positive"] = pos_list[:3]
                    
                if gemini_data.get("negative_highlights"):
                    result_data["aspects"][aspect]["highlights"]["negative"] = gemini_data["negative_highlights"]
                else:
                    result_data["aspects"][aspect]["highlights"]["negative"] = neg_list[:3]
            except Exception as e:
                print(f"[WARNING] Gemini summary error for {aspect}: {e}")
                result_data["aspects"][aspect]["summary"] = "Hệ thống AI đang quá tải."
                result_data["aspects"][aspect]["highlights"]["positive"] = pos_list[:3]
                result_data["aspects"][aspect]["highlights"]["negative"] = neg_list[:3]
        else:
            result_data["aspects"][aspect]["summary"] = "Không có bình luận nào về khía cạnh này."
            result_data["aspects"][aspect]["highlights"]["positive"] = pos_list[:3]
            result_data["aspects"][aspect]["highlights"]["negative"] = neg_list[:3]

    return result_data

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)

