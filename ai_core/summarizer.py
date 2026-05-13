import os
import json
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

class ReviewSummarizer:
    def __init__(self, gemini_key=None, gemma_key=None):
        self.gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY")
        self.gemma_key = gemma_key or os.environ.get("GEMMA_API_KEY", "gemma4-openclaw-2026")
        
        # Khởi tạo Gemini Client (Lựa chọn 1)
        self.gemini_client = None
        if self.gemini_key and self.gemini_key != "YOUR_GEMINI_API_KEY_HERE":
            self.gemini_client = genai.Client(api_key=self.gemini_key)
            
        # Khởi tạo Gemma Client (Lựa chọn 2 - Dự phòng)
        self.gemma_client = OpenAI(
            base_url="http://171.226.10.121:8000/llm/v1",
            api_key=self.gemma_key
        )

    def summarize_and_extract(self, aspect, positive_comments, negative_comments):
        """
        Gửi danh sách bình luận Khen/Chê của 1 khía cạnh cho AI tóm tắt.
        Lựa chọn 1: Thử gọi Gemini.
        Lựa chọn 2: Nếu Gemini lỗi (hết Quota), tự động gọi Gemma 4.
        """
        if not positive_comments and not negative_comments:
            return {
                "summary": "Không có đánh giá nào cho khía cạnh này.",
                "positive_highlights": [],
                "negative_highlights": []
            }

        prompt = f"""
Bạn là chuyên gia phân tích đánh giá sản phẩm.
Tóm tắt ngắn gọn Ưu/Nhược điểm về khía cạnh '{aspect}' từ các bình luận dưới đây.
Đồng thời trích xuất tối đa 5 câu khen nổi bật nhất và 5 câu chê nổi bật nhất (trích nguyên văn, ngắn gọn).

Bình luận Tích cực:
{positive_comments[:20]}

Bình luận Tiêu cực:
{negative_comments[:20]}

Trả về kết quả bằng ĐÚNG ĐỊNH DẠNG JSON sau, không giải thích gì thêm:
{{
  "summary": "Đánh giá chung...",
  "positive_highlights": ["câu khen 1", "câu khen 2", "câu khen 3", "câu khen 4", "câu khen 5"],
  "negative_highlights": ["câu chê 1", "câu chê 2", "câu chê 3", "câu chê 4", "câu chê 5"]
}}
"""
        fallback_result = {
            "summary": "Hệ thống AI hiện đang quá tải. Dưới đây là các bình luận thô đã được lọc:",
            "positive_highlights": positive_comments[:5],
            "negative_highlights": negative_comments[:5]
        }
        
        # --- LỰA CHỌN 1: GEMINI API ---
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3].strip()
                elif text.startswith("```"):
                    text = text[3:-3].strip()
                
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    return json.loads(text[start_idx:end_idx+1])
            except Exception as e:
                print(f"Gemini API Error (Chuyển sang dùng Gemma): {e}")
        else:
            print("Không tìm thấy Gemini Key, tự động chuyển sang Gemma...")

        # --- LỰA CHỌN 2: GEMMA 4 MoE (DỰ PHÒNG) ---
        try:
            response = self.gemma_client.chat.completions.create(
                model="gemma-4",
                messages=[
                    {"role": "system", "content": "Bạn trả về kết quả định dạng JSON thuần túy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.1
            )
            text = response.choices[0].message.content.strip()
            
            # Cắt JSON chuẩn xác để tránh lỗi Extra data
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                return json.loads(text[start_idx:end_idx+1])
            else:
                return fallback_result
                
        except Exception as e:
            print(f"Gemma API Error: {e}")
            return fallback_result

if __name__ == "__main__":
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("Chưa đặt biến môi trường GEMINI_API_KEY. Thoát.")
        exit(1)

    try:
        summarizer = ReviewSummarizer(api_key=API_KEY)
        
        # Giả lập dữ liệu mà PhoBERT vừa bóc tách ra được
        khia_canh_dang_xet = "Chất lượng sản phẩm"
        nhung_cau_khen = [
            "Điện thoại xài rất mượt, màn hình đẹp.",
            "Cầm rất đầm tay và xịn xò nha mọi người, đáng đồng tiền.",
            "Chụp ảnh khá nét, pin trâu."
        ]
        nhung_cau_che = [
            "Xài được 2 ngày đã hỏng màn hình.",
            "Máy hơi nóng khi chơi game lâu.",
            "Ốp lưng tặng kèm bị ố vàng hết trơn."
        ]
        
        print(f"Đang nhờ Gemini đọc và tóm tắt khía cạnh: {khia_canh_dang_xet}...\n")
        
        # Gọi hàm tóm tắt
        ket_qua = summarizer.summarize(khia_canh_dang_xet, nhung_cau_khen, nhung_cau_che)
        
        print("ĐOẠN TÓM TẮT DÀNH CHO NGƯỜI DÙNG:")
        print("=>", ket_qua)
        
    except Exception as e:
        print(e)
