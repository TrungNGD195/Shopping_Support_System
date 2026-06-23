from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import uvicorn
from contextlib import asynccontextmanager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from ai_core.inference import ABSAPredictor, SpamPredictor
from ai_core.summarizer import ReviewSummarizer
from src.scraper import get_reviews_from_url

summarizer = None
try:
    _ai_core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai_core")
    if _ai_core_path not in sys.path:
        sys.path.append(_ai_core_path)
    from summarizer import ReviewSummarizer
except ImportError:
    ReviewSummarizer = None

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
        
    api_key = "AIzaSyBjaku1UOU39XLS2IhIJolUSEtCcfFGYo8"
    
    gemma_key = "gemma4-openclaw-2026"
    summarizer = ReviewSummarizer(gemma_key=gemma_key)
    print("[INFO] Da nap thanh cong mo hinh AI va Gemma Summarizer!")
    yield
    ai_station = None
    spam_station = None
    summarizer = None

app = FastAPI(title="Shopping Support System API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str
    reviews_data: list = None

@app.post("/api/analyze")
def analyze_product(request: AnalyzeRequest):
    url = request.url
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    if request.reviews_data:
        comments = [str(r.get("comment", "")).strip() for r in request.reviews_data if len(str(r.get("comment", "")).strip()) > 5]
    else:
        comments = get_reviews_from_url(url)
    
    if not comments:
        raise HTTPException(status_code=404, detail="Không tìm thấy bình luận nào cho sản phẩm này.")

    def get_product_info(product_url: str):
        import requests, re, urllib.parse
        info = {
            "name": "Sản phẩm Demo",
            "image": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?q=80&w=1000&auto=format&fit=crop"
        }
        
        if request.reviews_data:
            for r in request.reviews_data:
                if r.get("product_items") and isinstance(r["product_items"], list) and len(r["product_items"]) > 0:
                    item = r["product_items"][0]
                    if item.get("name"):
                        info["name"] = item.get("name")
                    if item.get("image"):
                        info["image"] = "https://down-vn.img.susercontent.com/file/" + item.get("image")
                    return info

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
                    search_name = " ".join(name.split(" ")[:8]) + " shopee"
                    
                    try:
                        from ddgs import DDGS 
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
            "total_analyzed_comments": 0, 
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

    def format_highlight(cmt: str) -> str:
        import re
        c = str(cmt)
        
        c = re.sub(r'([:,])([^\s/0-9])', r'\1 \2', c)
        
        c = re.sub(r'\s+', ' ', c).strip()
        c = re.sub(r'([.?!])\1+', r'\1', c)
        
        if c:
            c = c[0].upper() + c[1:]
        return c

    def is_spam(text: str) -> bool:
        text_lower = str(text).lower()
        real_keywords = [
            "vải", "chất", "đẹp", "xấu", "màu", "size", "form", "mặc", "quần", "áo", "chỉ", "may", "mỏng", "dày", "cứng", "mềm", "mịn", "xù", "nóng", "mát", "rộng", "chật", "ngắn", "dài",
            
            "nồi", "máy", "thiết", "kế", "dùng", "sử", "dụng", "cắm", "điện", "bảo", "hành", "lỗi", "hư", "hỏng", "chạy", "êm", "ồn", "giặt", "sạch", "pin", "sạc", "màn", "âm", "thanh", "chuẩn", "khét", "nấu", "chín", "sôi", "bếp", "nướng", "quạt",
            
            "kính", "cường", "lực", "ốp", "lưng", "dán", "viền", "trầy", "xước", "cảm", "ứng", "mượt",
            
            "rẻ", "đắt", "giao", "shop", "gói", "tư", "vấn", "thơm", "xịn", "ok", "tốt", "ưng", "nhanh", "chậm", "mua", "test", "hàng", "tiền", "giá", "chắc", "bền", "thích", "tuyệt", "kém", "tệ", "tạm", "ổn", "khen", "chê", "thất", "vọng", "hài", "lòng", "đáng", "phí", "xứng", "lượng", "đóng", "cẩn", "thận", "nhẹ", "nặng", "to", "nhỏ", "thật", "giả", "nhái", "chính", "hãng", "hình", "ảnh", "video"
        ]
        real_count = sum(1 for kw in real_keywords if kw in text_lower)
        
        if len(text_lower) > 200 and real_count < 5:
            return True
        if len(text_lower) > 100 and real_count == 0:
            return True
            
        if any(kw in text_lower for kw in ["nhận xu", "lấy xu", "săn xu", "mang tính chất", "chống trôi", "hình ảnh mang tính"]):
            if real_count < 2 and not (len(text_lower) > 50 and real_count >= 1): 
                return True
            
        if len(text_lower.strip()) < 5: return True

        if spam_station:
            return spam_station.is_spam(text)
            
        return False

    import random
    MAX_COMMENTS = 100
    
    random.seed(42)
    shuffled_comments = comments.copy()
    random.shuffle(shuffled_comments)

    valid_comments = []
    for cmt in shuffled_comments:
        if not is_spam(cmt):
            valid_comments.append(cmt)
            if len(valid_comments) >= MAX_COMMENTS:
                break
                
            
    result_data["overview"]["total_analyzed_comments"] = len(valid_comments)

    overview_khen = 0
    overview_che = 0

    batch_predictions = ai_station.predict_batch(valid_comments, batch_size=32)

    for idx, cmt in enumerate(valid_comments):
        prediction = batch_predictions[idx]
        
        has_khen = False
        has_che = False

        for aspect in result_data["aspects"]:
            sentiment = prediction.get(aspect)
            formatted_cmt = format_highlight(cmt)
            
            if sentiment == "Tích cực (Khen)":
                result_data["aspects"][aspect]["stats"]["Khen"] += 1
                result_data["aspects"][aspect]["highlights"]["positive"].append(formatted_cmt)
                has_khen = True
            elif sentiment == "Tiêu cực (Chê)":
                result_data["aspects"][aspect]["stats"]["Chê"] += 1
                result_data["aspects"][aspect]["highlights"]["negative"].append(formatted_cmt)
                has_che = True
            elif sentiment == "Bình thường":
                result_data["aspects"][aspect]["stats"]["Bình thường"] += 1
            else:
                result_data["aspects"][aspect]["stats"]["Không nhắc tới"] += 1
                
        if has_khen:
            overview_khen += 1
        if has_che:
            overview_che += 1

    if overview_khen > overview_che:
        verdict_html = "<span class='verdict-good'>🟢 Rất Đáng Mua</span>"
    elif overview_che > overview_khen:
        verdict_html = "<span class='verdict-bad'>🔴 Cần Cân Nhắc</span>"
    else:
        verdict_html = "<span class='verdict-neutral'>🟡 Phân vân (Trung lập)</span>"

    result_data["overview"]["final_verdict"] = verdict_html
    result_data["overview"]["total_khen"] = overview_khen
    result_data["overview"]["total_che"] = overview_che

    import concurrent.futures

    def summarize_aspect(aspect_key):
        pos_list = list(dict.fromkeys(result_data["aspects"][aspect_key]["highlights"]["positive"]))[:10]
        neg_list = list(dict.fromkeys(result_data["aspects"][aspect_key]["highlights"]["negative"]))[:10]
        vi_name = result_data["aspects"][aspect_key]["name"]
        
        if summarizer and (pos_list or neg_list):
            try:
                gemini_data = summarizer.summarize_and_extract(vi_name, pos_list, neg_list)
                result_data["aspects"][aspect_key]["summary"] = gemini_data.get("summary", "Không thể tóm tắt.")
                
                if gemini_data.get("positive_highlights"):
                    result_data["aspects"][aspect_key]["highlights"]["positive"] = gemini_data["positive_highlights"]
                else:
                    result_data["aspects"][aspect_key]["highlights"]["positive"] = pos_list[:5]
                    
                if gemini_data.get("negative_highlights"):
                    result_data["aspects"][aspect_key]["highlights"]["negative"] = gemini_data["negative_highlights"]
                else:
                    result_data["aspects"][aspect_key]["highlights"]["negative"] = neg_list[:5]
            except Exception as e:
                print(f"[WARNING] Summary error for {aspect_key}: {e}")
                result_data["aspects"][aspect_key]["summary"] = "Hệ thống AI đang quá tải."
                result_data["aspects"][aspect_key]["highlights"]["positive"] = pos_list[:5]
                result_data["aspects"][aspect_key]["highlights"]["negative"] = neg_list[:5]
        else:
            result_data["aspects"][aspect_key]["summary"] = "Không có bình luận nào về khía cạnh này."
            result_data["aspects"][aspect_key]["highlights"]["positive"] = pos_list[:5]
            result_data["aspects"][aspect_key]["highlights"]["negative"] = neg_list[:5]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(summarize_aspect, aspect) for aspect in result_data["aspects"]]
        concurrent.futures.wait(futures)

    return result_data

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)

