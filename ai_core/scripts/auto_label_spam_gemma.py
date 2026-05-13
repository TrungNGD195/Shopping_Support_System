import os
import time
import json
import pandas as pd
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

def label_spam_with_gemma(input_csv="../../data/spam_dataset.csv", output_csv="../../data/gemma_labeled_spam.csv", limit=None):
    client = OpenAI(
        base_url="http://171.226.10.121:8000/llm/v1",
        api_key="gemma4-openclaw-2026"
    )
    
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy {input_csv}. Vui lòng kiểm tra đường dẫn.")
        return

    if limit is not None:
        df = df.head(limit).copy()
    
    # Thêm cột kết quả của Gemma
    if 'gemma_is_spam' not in df.columns:
        df['gemma_is_spam'] = -1

    prompt_template = """
Bạn là hệ thống lọc bình luận rác (Spam Filter) cho sàn thương mại điện tử.
Phân loại bình luận dưới đây là RÁC (0) hay THẬT (1).

Quy tắc:
- 0 (Rác/Spam): Chứa thơ ca, bài hát, văn mẫu kiếm xu không liên quan ("Hình ảnh mang tính chất nhận xu", "Xin phép nhận xu", "Giao hàng nhanh nhưng chất lượng để sau"). Hoặc các đoạn ký tự vô nghĩa ("hjshdfsjf", ".......").
- 1 (Thật): Bình luận có nhận xét rõ ràng về sản phẩm, giao hàng, thái độ shop (Ví dụ: "Áo đẹp, vải mát", "Giao sai màu", "Nồi dùng tốt", "Hơi chật").

Trả về ĐÚNG định dạng JSON sau, không giải thích thêm:
{{
    "is_spam": 0  // hoặc 1
}}

Bình luận:
"{comment}"
"""

    print(f"Bắt đầu gán nhãn SPAM cho {len(df)} dòng bằng Gemma 4 (1000 luồng)...")
    
    indices = df.index.tolist()
    print_lock = Lock()
    success_count = 0
    
    def process_row(index):
        nonlocal success_count
        row = df.loc[index]
        comment = str(row['comment'])
        
        if len(comment.strip()) < 2:
            return index, 0
            
        prompt = prompt_template.format(comment=comment)
        
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gemma-4",
                    messages=[
                        {"role": "system", "content": "Bạn trả về kết quả định dạng JSON thuần túy."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=128,
                    temperature=0.0
                )
                
                text = response.choices[0].message.content.strip()
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = text[start_idx:end_idx+1]
                    result = json.loads(json_str)
                    
                    raw_label = result.get('is_spam', -1)
                    if isinstance(raw_label, list): label = int(raw_label[0]) if len(raw_label) > 0 else -1
                    else:
                        try: label = int(raw_label)
                        except (ValueError, TypeError): label = -1
                else:
                    raise ValueError("Không tìm thấy JSON hợp lệ")
                    
                with print_lock:
                    success_count += 1
                    status = "SPAM" if label == 0 else "THẬT" if label == 1 else "LỖI"
                    print(f"[{success_count}/{len(df)}] {status}: {comment[:40]}...")
                    
                return index, label
                
            except Exception as e:
                if attempt == 2:
                    with print_lock:
                        success_count += 1
                        print(f"[{success_count}/{len(df)}] Lỗi API: '{comment[:30]}...' -> {e}")
                time.sleep(0.5)
                
        return index, -1

    with ThreadPoolExecutor(max_workers=1000) as executor:
        futures = {executor.submit(process_row, idx): idx for idx in indices}
        
        for future in as_completed(futures):
            idx, label = future.result()
            df.at[idx, 'gemma_is_spam'] = label
            
    df.to_csv(output_csv, index=False)
    
    total_spam = len(df[df['gemma_is_spam'] == 0])
    total_real = len(df[df['gemma_is_spam'] == 1])
    
    print(f"\\nHOÀN TẤT! Đã phát hiện {total_spam} Spam và {total_real} đánh giá Thật.")
    print(f"Kết quả lưu tại: {output_csv}")

if __name__ == "__main__":
    # Đọc file dataset đã tạo từ script cũ (gồm 26k review cả thật và spam)
    # Lưu ra file mới là gemma_labeled_spam.csv
    label_spam_with_gemma(
        input_csv="../../data/spam_dataset.csv", 
        output_csv="../../data/gemma_labeled_spam.csv", 
        limit=None
    )
