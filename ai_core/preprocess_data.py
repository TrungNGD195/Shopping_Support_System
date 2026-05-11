import pandas as pd
import re
import os
import sys

# Đặt mã hóa UTF-8 cho console để tránh lỗi in chữ tiếng Việt trên Windows
sys.stdout.reconfigure(encoding='utf-8')

try:
    from pyvi import ViTokenizer
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyvi"])
    from pyvi import ViTokenizer

def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    # Chuyển về chữ thường
    text = text.lower()
    
    # Xóa các ký tự đặc biệt, emoji, giữ lại chữ, số và khoảng trắng, dấu phẩy, chấm
    text = re.sub(r'[^\w\s\.,!?áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]', ' ', text)
    
    # Chuẩn hóa teencode phổ biến
    teencode_dict = {
        r'\bko\b': 'không',
        r'\bk\b': 'không',
        r'\bkh\b': 'không',
        r'\bkhg\b': 'không',
        r'\bdc\b': 'được',
        r'\bđc\b': 'được',
        r'\bok\b': 'tốt',
        r'\boke\b': 'tốt',
        r'\bsp\b': 'sản phẩm',
        r'\bshop\b': 'cửa hàng',
        r'\btk\b': 'tiki',
        r'\btiki\b': 'tiki',
        r'\bshopee\b': 'shopee',
        r'\bauth\b': 'chính hãng',
        r'\bchuẩn\b': 'chính hãng',
        r'\bgiao\b': 'giao hàng',
        r'\bship\b': 'giao hàng',
        r'\bđt\b': 'điện thoại',
        r'\bmk\b': 'mình',
        r'\bm\b': 'mình',
        r'\bt\b': 'tôi',
        r'\bhj\b': 'hàng',
        r'\bh\b': 'giờ',
        r'\bvs\b': 'với'
    }
    
    for pattern, replace in teencode_dict.items():
        text = re.sub(pattern, replace, text)
    
    # Xóa khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Tokenize từ tiếng Việt (phục vụ cho PhoBERT)
    text = ViTokenizer.tokenize(text)
    
    return text

def main():
    data_dir = r"d:\Shopping_Support_System\data"
    files = ["negative_reviews.csv", "positive_reviews.csv"]
    
    for file in files:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            print(f"Đang xử lý file: {file}...")
            df = pd.read_csv(file_path)
            
            # Giữ lại các comment không bị rỗng
            df = df.dropna(subset=['comment'])
            
            # Áp dụng hàm clean_text
            df['cleaned_comment'] = df['comment'].apply(clean_text)
            
            # Lọc bỏ các dòng sau khi clean bị rỗng
            df = df[df['cleaned_comment'].str.strip() != '']
            
            # Lưu ra file mới
            output_file = os.path.join(data_dir, f"cleaned_{file}")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Đã lưu file chuẩn hóa: {output_file} (Tổng số dòng: {len(df)})")
        else:
            print(f"Không tìm thấy file: {file_path}")

if __name__ == "__main__":
    main()
