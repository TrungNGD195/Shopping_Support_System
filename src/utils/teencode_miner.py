import pandas as pd
import re
from collections import Counter

def find_top_words(csv_path, text_column='comment'):
    print(f"🔍 Đang đọc file dữ liệu: {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
        
        if text_column not in df.columns:
            print(f"❌ Lỗi: Không tìm thấy cột '{text_column}' trong file CSV.")
            print(f"Các cột hiện có: {list(df.columns)}")
            return
            
        all_text = " ".join(df[text_column].dropna().astype(str).tolist())
        
        all_text = all_text.lower()
        all_text = re.sub(r'[^\w\sđăâêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]', ' ', all_text)
        all_text = re.sub(r'\d+', ' ', all_text)
        
        words = all_text.split()
        
        word_counts = Counter(words)
        
        print("\n--- 🏆 TOP 150 TỪ PHỔ BIẾN NHẤT ---")
        for word, freq in word_counts.most_common(150):
            print(f"{word} : {freq} lần")
            
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    dummy_data = {
        'comment': [
            "áo đẹpppp sp xịn lắm sóp ơi", 
            "hàng lởm k giống hình auth gì cả", 
            "sp này xài dc nha mn",
            "giao ship nhanh nt tư vấn nhiệt tình",
            "k mua nữa đâu sóp làm ăn chán"
        ]
    }
    df_dummy = pd.DataFrame(dummy_data)
    df_dummy.to_csv('dummy_test.csv', index=False)
    
    find_top_words('dummy_test.csv', text_column='comment')