from google import genai
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

class ReviewSummarizer:
    def __init__(self, api_key=None):
        # Lấy API Key từ tham số, hoặc từ biến môi trường
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY_HERE":
            raise ValueError("Chưa cấu hình Gemini API Key. Vui lòng thêm API Key vào code!")
            
        # Khởi tạo client theo chuẩn thư viện google-genai mới nhất
        self.client = genai.Client(api_key=self.api_key)

    def summarize(self, aspect, positive_comments, negative_comments):
        """
        Gửi danh sách bình luận Khen/Chê của 1 khía cạnh cho Gemini tóm tắt.
        """
        # Nếu không có bình luận nào thì bỏ qua
        if not positive_comments and not negative_comments:
            return "Không có đánh giá nào cho khía cạnh này."

        # Xây dựng câu lệnh (Prompt) ép AI làm theo ý mình
        prompt = f"""
        Bạn là một reviewer công nghệ/chuyên gia mua sắm cực kỳ có tâm trên Shopee.
        Tôi có một sản phẩm với các bình luận của khách hàng về khía cạnh '{aspect}'.
        Hãy viết MỘT ĐOẠN VĂN DUY NHẤT (tầm 3-4 câu) tóm tắt lại cảm nhận chung của mọi người.
        
        YÊU CẦU BẮT BUỘC:
        - Giọng văn tự nhiên, mượt mà, giống như một reviewer đang khuyên bạn bè (ví dụ: "Nhìn chung mọi người đều khen...", "Điểm trừ lớn nhất là...").
        - Không gạch đầu dòng, không xưng "tôi" hay "bạn".
        - Tổng hợp mượt mà cả khen và chê vào chung 1 đoạn văn.

        Danh sách các lời KHEN:
        {chr(10).join(['- ' + c for c in positive_comments]) if positive_comments else 'Không có lời khen nào.'}

        Danh sách các lời CHÊ/PHÀN NÀN:
        {chr(10).join(['- ' + c for c in negative_comments]) if negative_comments else 'Không có lời chê nào.'}
        
        Hãy viết đoạn tóm tắt thật hay:
        """
        
        try:
            # Sử dụng model gemini-flash-latest (tự động chọn phiên bản có hỗ trợ free tier)
            response = self.client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Lỗi khi gọi API: {str(e)}"

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
