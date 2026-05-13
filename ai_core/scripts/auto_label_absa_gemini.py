import os
import time
import json
import pandas as pd
from pydantic import BaseModel
from google import genai
from google.genai import types

# Cấu hình API Key (Lấy từ biến môi trường hoặc điền trực tiếp)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY")

class ABSAResult(BaseModel):
    Quality: int
    Price: int
    Delivery: int
    Service: int

def label_dataset_with_gemini(input_csv="data/cleaned_negative_reviews.csv", output_csv="data/gemini_labeled_negative.csv", limit=1000):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
        print("Vui lòng thiết lập GEMINI_API_KEY trước khi chạy!")
        return
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Đọc data cần gán nhãn
    df = pd.read_csv(input_csv)
    if limit is not None:
        df = df.head(limit).copy()
    
    # Khởi tạo các cột mới
    for aspect in ["Quality", "Price", "Delivery", "Service"]:
        df[aspect] = -1

    prompt_template = """
Bạn là một chuyên gia phân tích cảm xúc bình luận thương mại điện tử (ABSA).
Hãy phân loại bình luận dưới đây vào 4 khía cạnh: Quality (Chất lượng sản phẩm), Price (Giá cả), Delivery (Vận chuyển/Đóng gói), Service (Dịch vụ khách hàng của Shop).

Mỗi khía cạnh chỉ được nhận 1 trong 4 nhãn số sau:
-1: Không nhắc tới (Bắt buộc dùng nhãn này nếu khách không hề đề cập đến khía cạnh đó)
0: Tiêu cực (Chê bai, phàn nàn, móp méo, hư hỏng, sai hàng, thái độ lồi lõm)
1: Bình thường (Trung lập, không khen không chê, tạm ổn)
2: Tích cực (Khen ngợi, xuất sắc, nhiệt tình, đóng gói kỹ)

LƯU Ý ĐẶC BIỆT:
- "Giao hàng lâu", "Hộp móp méo": Là Tiêu cực (0) của Delivery.
- "Giao sai mẫu", "Thái độ shop tệ": Là Tiêu cực (0) của Service.
- "Giá rẻ nhưng xài chán": Price là 2 (Khen), Quality là 0 (Chê).
- Đọc kỹ ngữ cảnh: "Kính cường lực mỏng" là Khen (2), nhưng "Áo thun quá mỏng" là Chê (0).
- Trả về đúng định dạng JSON.

Bình luận cần phân tích:
"{comment}"
"""

    print(f"Bắt đầu gán nhãn cho {len(df)} dòng dữ liệu bằng Gemini...")
    
    for index, row in df.iterrows():
        comment = str(row['comment'])
        if len(comment.strip()) < 2:
            continue
            
        prompt = prompt_template.format(comment=comment)
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ABSAResult,
                    temperature=0.1
                ),
            )
            
            result = json.loads(response.text)
            df.at[index, 'Quality'] = result.get('Quality', -1)
            df.at[index, 'Price'] = result.get('Price', -1)
            df.at[index, 'Delivery'] = result.get('Delivery', -1)
            df.at[index, 'Service'] = result.get('Service', -1)
            
            print(f"[{index+1}/{len(df)}] Thành công: {comment[:30]}... -> Q:{result.get('Quality')} | P:{result.get('Price')} | D:{result.get('Delivery')} | S:{result.get('Service')}")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"[{index+1}/{len(df)}] Lỗi API với bình luận: '{comment[:30]}...' -> {e}")
            time.sleep(5)
            
    # Lưu file
    df.to_csv(output_csv, index=False)
    print(f"\\nHOÀN TẤT! Đã lưu kết quả gán nhãn chuẩn vào {output_csv}")

if __name__ == "__main__":
    # Gán nhãn cho file bình luận tiêu cực
    label_dataset_with_gemini(
        input_csv="../../data/cleaned_negative_reviews.csv", 
        output_csv="../../data/gemini_labeled_negative.csv", 
        limit=50
    )
    
    # Gán nhãn cho file bình luận tích cực
    label_dataset_with_gemini(
        input_csv="../../data/cleaned_positive_reviews.csv", 
        output_csv="../../data/gemini_labeled_positive.csv", 
        limit=50
    )
