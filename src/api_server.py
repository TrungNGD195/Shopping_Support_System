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

from ai_core.inference import ABSAPredictor
from ai_core.summarizer import ReviewSummarizer
from src.scraper import get_reviews_from_url

# Khởi tạo mô hình AI (Load 1 lần duy nhất khi server start)
ai_station = None
summarizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_station, summarizer
    print("[INFO] Dang nap mo hinh AI vao RAM...")
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'phobert-absa-final')
    ai_station = ABSAPredictor(model_dir)
    summarizer = ReviewSummarizer(api_key="AIzaSyAHtaMW99Y9qMTLtsqEgvLZNY47Y28GXio")
    print("[INFO] Da nap thanh cong mo hinh AI va Gemini Summarizer!")
    yield
    ai_station = None
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
    for cmt in comments:
        prediction = ai_station.predict(cmt) # Trả về {"Quality": "Tích cực (Khen)", ...}
        
        for aspect in result_data["aspects"]:
            sentiment = prediction.get(aspect)
            if sentiment == "Tích cực (Khen)":
                result_data["aspects"][aspect]["stats"]["Khen"] += 1
                result_data["aspects"][aspect]["highlights"]["positive"].append(cmt)
            elif sentiment == "Tiêu cực (Chê)":
                result_data["aspects"][aspect]["stats"]["Chê"] += 1
                result_data["aspects"][aspect]["highlights"]["negative"].append(cmt)
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

    # 4. Yêu cầu Gemini tóm tắt cho từng khía cạnh
    for aspect in result_data["aspects"]:
        pos_list = list(set(result_data["aspects"][aspect]["highlights"]["positive"]))
        neg_list = list(set(result_data["aspects"][aspect]["highlights"]["negative"]))
        
        # Gán lại list đã khử trùng
        result_data["aspects"][aspect]["highlights"]["positive"] = pos_list
        result_data["aspects"][aspect]["highlights"]["negative"] = neg_list
        
        # Lấy tên tiếng Việt
        vi_name = result_data["aspects"][aspect]["name"]
        
        if pos_list or neg_list:
            summary_text = summarizer.summarize(vi_name, pos_list, neg_list)
            result_data["aspects"][aspect]["summary"] = summary_text
        else:
            result_data["aspects"][aspect]["summary"] = "Không có bình luận nào về khía cạnh này."

    return result_data

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)

