import os
import time
import json
import pandas as pd
from pydantic import BaseModel
from openai import OpenAI

class ABSAResult(BaseModel):
    Quality: int
    Price: int
    Delivery: int
    Service: int

def label_dataset_with_gemma(input_csv="data/cleaned_negative_reviews.csv", output_csv="data/gemma_labeled_negative.csv", limit=1000):
    client = OpenAI(
        base_url="http://171.226.10.121:8000/llm/v1",
        api_key="gemma4-openclaw-2026"
    )
    
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
- BẮT BUỘC TRẢ VỀ ĐÚNG ĐỊNH DẠNG JSON. Không viết thêm chữ nào khác ngoài JSON.

Bình luận cần phân tích:
"{comment}"
"""

    from concurrent.futures import ThreadPoolExecutor, as_completed
    from threading import Lock
    
    print(f"Bắt đầu gán nhãn cho {len(df)} dòng dữ liệu bằng Gemma 4 (Chạy song song 1000 luồng)...")
    
    # Chuẩn bị danh sách index để chạy
    indices = df.index.tolist()
    
    # Lock để in tiến độ không bị chồng chéo
    print_lock = Lock()
    success_count = 0
    
    def process_row(index):
        nonlocal success_count
        row = df.loc[index]
        comment = str(row['comment'])
        
        if len(comment.strip()) < 2:
            return index, -1, -1, -1, -1
            
        prompt = prompt_template.format(comment=comment)
        
        for attempt in range(3): # Thử lại tối đa 3 lần nếu lỗi
            try:
                response = client.chat.completions.create(
                    model="gemma-4",
                    messages=[
                        {"role": "system", "content": "Bạn trả về kết quả định dạng JSON thuần túy."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=256,
                    temperature=0.1
                )
                
                text = response.choices[0].message.content.strip()
                
                # Bóc tách chính xác phần JSON nằm giữa { và }
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = text[start_idx:end_idx+1]
                    result = json.loads(json_str)
                else:
                    raise ValueError("Gemma không trả về định dạng JSON hợp lệ")
                    
                with print_lock:
                    success_count += 1
                    print(f"[{success_count}/{len(df)}] Thành công: {comment[:30]}... -> Q:{result.get('Quality')} | P:{result.get('Price')} | D:{result.get('Delivery')} | S:{result.get('Service')}")
                    
                return index, result.get('Quality', -1), result.get('Price', -1), result.get('Delivery', -1), result.get('Service', -1)
                
            except Exception as e:
                if attempt == 2:
                    with print_lock:
                        success_count += 1
                        print(f"[{success_count}/{len(df)}] Lỗi API với bình luận: '{comment[:30]}...' -> {e}")
                time.sleep(1)
                
        return index, -1, -1, -1, -1

    # Chạy song song với 1000 threads
    with ThreadPoolExecutor(max_workers=1000) as executor:
        futures = {executor.submit(process_row, idx): idx for idx in indices}
        
        for future in as_completed(futures):
            idx, q, p, d, s = future.result()
            df.at[idx, 'Quality'] = q
            df.at[idx, 'Price'] = p
            df.at[idx, 'Delivery'] = d
            df.at[idx, 'Service'] = s
            
    # Lưu file
    df.to_csv(output_csv, index=False)
    print(f"\\nHOÀN TẤT! Đã lưu kết quả gán nhãn chuẩn vào {output_csv}")

if __name__ == "__main__":
    # Gán nhãn cho toàn bộ file bình luận tiêu cực
    label_dataset_with_gemma(
        input_csv="../../data/cleaned_negative_reviews.csv", 
        output_csv="../../data/gemma_labeled_negative.csv", 
        limit=None
    )
    
    # Gán nhãn cho toàn bộ file bình luận tích cực
    label_dataset_with_gemma(
        input_csv="../../data/cleaned_positive_reviews.csv", 
        output_csv="../../data/gemma_labeled_positive.csv", 
        limit=None
    )
