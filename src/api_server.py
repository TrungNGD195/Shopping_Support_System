from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import uvicorn
from contextlib import asynccontextmanager

# Đảm bảo có thể import module từ src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inference import ABSAPredictor
from scraper import get_reviews_from_url

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_station, summarizer
    print("[INFO] Dang nap mo hinh AI vao RAM...")
    ai_station = ABSAPredictor()

    # Try to initialize Gemini summarizer
    if ReviewSummarizer:
        try:
            summarizer = ReviewSummarizer()
            print("[INFO] Da nap thanh cong Gemini Summarizer!")
        except Exception as e:
            print(f"[WARNING] Khong the khoi dong Gemini Summarizer: {e}")
            summarizer = None
    else:
        print("[INFO] Gemini Summarizer khong kha dung (thieu thu vien hoac API key).")

    print("[INFO] Da nap thanh cong mo hinh AI!")
    yield
    # Clean up (nếu cần)
    ai_station = None
    summarizer = None

app = FastAPI(title="Shopping Support System API", lifespan=lifespan)

# Cấu hình CORS để cho phép React Web App gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Hoặc cụ thể ["http://localhost:5173"]
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

    # 1. Lấy dữ liệu bình luận (từ Scraper)
    comments = get_reviews_from_url(url)
    
    if not comments:
        raise HTTPException(status_code=404, detail="Không tìm thấy bình luận nào cho sản phẩm này.")

    # Cấu trúc JSON trả về chuẩn hóa
    result_data = {
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
                "summary": "Đánh giá chất liệu, độ bền và kiểu dáng sản phẩm."
            },
            "Price": {
                "name": "Giá cả", "icon": "💰", 
                "stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, 
                "highlights": {"positive": [], "negative": []}, 
                "summary": "Đánh giá mức giá so với giá trị thực mang lại."
            },
            "Delivery": {
                "name": "Giao hàng", "icon": "🚚", 
                "stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, 
                "highlights": {"positive": [], "negative": []}, 
                "summary": "Đánh giá tốc độ giao nhận và quy cách đóng gói."
            },
            "Service": {
                "name": "Dịch vụ", "icon": "🎧", 
                "stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, 
                "highlights": {"positive": [], "negative": []}, 
                "summary": "Đánh giá thái độ hỗ trợ và tư vấn của shop."
            }
        }
    }

    # 2. Phân tích qua AI Station
    for cmt in comments:
        prediction = ai_station.predict_single_comment(cmt)
        
        # Bóc tách kết quả cho từng khía cạnh
        for aspect, data in prediction["aspects"].items():
            if aspect not in result_data["aspects"]: continue
            
            # Dùng label số (2=Khen, 1=Bình thường, 0=Chê, -1=Không nhắc tới)
            label_val = data.get('label', -1)
            
            if label_val == 2:
                result_data["aspects"][aspect]["stats"]["Khen"] += 1
                result_data["aspects"][aspect]["highlights"]["positive"].append(cmt)
            elif label_val == 0:
                result_data["aspects"][aspect]["stats"]["Chê"] += 1
                result_data["aspects"][aspect]["highlights"]["negative"].append(cmt)
            elif label_val == 1:
                result_data["aspects"][aspect]["stats"]["Bình thường"] += 1
            else:  # -1: Không nhắc tới
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

    # Loại bỏ duplicate highlight để giảm tải giao diện
    for aspect in result_data["aspects"]:
        result_data["aspects"][aspect]["highlights"]["positive"] = list(set(result_data["aspects"][aspect]["highlights"]["positive"]))
        result_data["aspects"][aspect]["highlights"]["negative"] = list(set(result_data["aspects"][aspect]["highlights"]["negative"]))

    # 4. Gọi Gemini API để tóm tắt từng khía cạnh (nếu có summarizer)
    if summarizer:
        for aspect_key, aspect_data in result_data["aspects"].items():
            pos = aspect_data["highlights"]["positive"]
            neg = aspect_data["highlights"]["negative"]
            if pos or neg:
                try:
                    summary = summarizer.summarize(aspect_data["name"], pos, neg)
                    result_data["aspects"][aspect_key]["summary"] = summary
                except Exception as e:
                    print(f"[WARNING] Gemini summary error for {aspect_key}: {e}")

    return result_data

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)

