import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

class ReviewSummarizer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMMA_API_KEY", "gemma4-openclaw-2026")
            
        # Khởi tạo client theo chuẩn OpenAI cho Gemma 4
        self.client = OpenAI(
            base_url="http://171.226.10.121:8000/llm/v1",
            api_key=self.api_key
        )

    def summarize_and_extract(self, aspect, positive_comments, negative_comments):
        """
        Gửi danh sách bình luận Khen/Chê của 1 khía cạnh cho Gemini tóm tắt VÀ trích xuất các câu nổi bật nhất.
        """
        import json
        if not positive_comments and not negative_comments:
            return {
                "summary": "Không có đánh giá nào cho khía cạnh này.",
                "positive_highlights": [],
                "negative_highlights": []
            }

        prompt = f"""
        Bạn là hệ thống phân tích đánh giá sản phẩm.
        Khía cạnh đang phân tích: '{aspect}'.

        Nhiều bình luận dưới đây rất dài và chứa thông tin của các khía cạnh khác (ví dụ: đang xét Giá Cả nhưng bình luận lại nói cả về Giao Hàng).
        
        NHIỆM VỤ:
        1. Tóm tắt cảm nhận chung (3-4 câu) CHỈ về khía cạnh '{aspect}'.
        2. Trích xuất tối đa 5 câu/cụm từ NGẮN (cắt bỏ phần thừa, chỉ lấy đúng phần nói về '{aspect}') đại diện cho Khen.
        3. Trích xuất tối đa 5 câu/cụm từ NGẮN (chỉ lấy phần nói về '{aspect}') đại diện cho Chê.

        Danh sách KHEN: {positive_comments}
        Danh sách CHÊ: {negative_comments}
        
        BẮT BUỘC trả về ĐÚNG định dạng JSON (không có markdown ```json):
        {{
            "summary": "Đoạn tóm tắt...",
            "positive_highlights": ["câu khen 1", "câu khen 2", "câu khen 3", "câu khen 4", "câu khen 5"],
            "negative_highlights": ["câu chê 1", "câu chê 2", "câu chê 3", "câu chê 4", "câu chê 5"]
        }}
        """
        
        fallback_result = {
            "summary": "Hệ thống AI đang quá tải, không thể tóm tắt.",
            "positive_highlights": positive_comments[:5],
            "negative_highlights": negative_comments[:5]
        }
        
        try:
            response = self.client.chat.completions.create(
                model='gemma-4',
                messages=[
                    {"role": "system", "content": "Bạn là hệ thống phân tích đánh giá sản phẩm. Bạn trả về kết quả định dạng JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.1
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            
            data = json.loads(text)
            return data
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return fallback_result

if __name__ == "__main__":
    # BƯỚC 1: DÁN API KEY CỦA BẠN VÀO ĐÂY
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
