import os
import json
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

class ReviewSummarizer:
    def __init__(self, gemma_key=None):
        self.gemma_key = gemma_key or os.environ.get("GEMMA_API_KEY", "gemma4-openclaw-2026")
            
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
Bạn là chuyên gia phân tích đánh giá sản phẩm. Nhiệm vụ của bạn là kiểm tra, lọc và tóm tắt các đánh giá.

CHÚ Ý ĐẶC BIỆT: Khía cạnh đang xét là: '{aspect}'.

QUY TẮC LỌC Ý KIẾN TIÊU BIỂU (TỐI QUAN TRỌNG):
Bạn nhận được một danh sách các bình luận bên dưới. Có thể hệ thống máy học trước đó đã phân loại NHẦM một số bình luận vào khía cạnh '{aspect}'. 
Nhiệm vụ của bạn là LỌC VÀ LOẠI BỎ hoàn toàn những bình luận bị phân loại nhầm.
- Nếu bình luận là "Bình quá đẹp, hơi nhỏ...", "Giữ nhiệt tốt..." -> KHÔNG PHẢI LÀ GIAO HÀNG. Bỏ ngay!
- Nếu bình luận là "Uống hơi khó...", "Màu sắc không tươi..." -> KHÔNG PHẢI LÀ GIAO HÀNG. Bỏ ngay!
- CHỈ GIỮ LẠI những câu thực sự nhắc đến '{aspect}'. Ví dụ nếu là Giao hàng thì phải có chữ "giao", "shipper", "nhanh", "chậm", "hộp", "đóng gói", v.v...
- Nếu sau khi lọc không còn câu nào hợp lệ, hãy trả về mảng rỗng []. TUYỆT ĐỐI KHÔNG lấy đại bình luận sai khía cạnh đưa vào!

Bình luận Tích cực (Khen):
{positive_comments[:20]}

Bình luận Tiêu cực (Chê):
{negative_comments[:20]}

Trả về kết quả bằng ĐÚNG ĐỊNH DẠNG JSON sau, không giải thích gì thêm:
{{
  "summary": "Tóm tắt ngắn gọn Ưu/Nhược điểm (nếu có) về {aspect}...",
  "positive_highlights": ["câu khen chuẩn 1", "câu khen chuẩn 2"],
  "negative_highlights": ["câu chê chuẩn 1"]
}}
"""
        fallback_result = {
            "summary": "Hệ thống AI hiện đang quá tải. Dưới đây là các bình luận thô đã được lọc:",
            "positive_highlights": positive_comments[:5],
            "negative_highlights": negative_comments[:5]
        }
        
        try:
            response = self.gemma_client.chat.completions.create(
                model="gemma-4",
                messages=[
                    {"role": "system", "content": "Bạn trả về kết quả định dạng JSON thuần túy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.1
            )
            text = response.choices[0].message.content.strip()
            
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
    try:
        summarizer = ReviewSummarizer()
        
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
        
        ket_qua = summarizer.summarize(khia_canh_dang_xet, nhung_cau_khen, nhung_cau_che)
        
        print("ĐOẠN TÓM TẮT DÀNH CHO NGƯỜI DÙNG:")
        print("=>", ket_qua)
        
    except Exception as e:
        print(e)
