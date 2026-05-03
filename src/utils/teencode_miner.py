import pandas as pd
import re
from collections import Counter

def find_top_words(csv_path, text_column='comment'):
    print(f"🔍 Đang đọc file dữ liệu: {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
        
        # Kiểm tra xem cột chứa comment có tồn tại không
        if text_column not in df.columns:
            print(f"❌ Lỗi: Không tìm thấy cột '{text_column}' trong file CSV.")
            print(f"Các cột hiện có: {list(df.columns)}")
            return
            
        # Gom tất cả các comment lại thành một chuỗi văn bản khổng lồ
        # dropna() để bỏ qua các dòng bị trống
        all_text = " ".join(df[text_column].dropna().astype(str).tolist())
        
        # Chuyển thành chữ thường và chỉ giữ lại chữ cái (xóa số, xóa icon, dấu câu)
        all_text = all_text.lower()
        all_text = re.sub(r'[^\w\sđăâêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]', ' ', all_text)
        all_text = re.sub(r'\d+', ' ', all_text) # Xóa luôn số cho sạch
        
        words = all_text.split()
        
        # Đếm tần suất xuất hiện của từng từ
        word_counts = Counter(words)
        
        print("\n--- 🏆 TOP 150 TỪ PHỔ BIẾN NHẤT ---")
        for word, freq in word_counts.most_common(150):
            print(f"{word} : {freq} lần")
            
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    # GIẢ LẬP TEST THỬ BẰNG DỮ LIỆU MẪU
    # Tạo nhanh một DataFrame giả để test code xem chạy không
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
    
    # Chạy hàm dò tìm
    find_top_words('dummy_test.csv', text_column='comment')