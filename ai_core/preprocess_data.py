import pandas as pd
import re
import os
import sys

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
    
    text = text.lower()
    
    text = re.sub(r'[^\w\s\.,!?áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]', ' ', text)
    
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
    
    text = re.sub(r'\s+', ' ', text).strip()
    
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
            
            df = df.dropna(subset=['comment'])
            
            df['cleaned_comment'] = df['comment'].apply(clean_text)
            
            df = df[df['cleaned_comment'].str.strip() != '']
            
            output_file = os.path.join(data_dir, f"cleaned_{file}")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Đã lưu file chuẩn hóa: {output_file} (Tổng số dòng: {len(df)})")
        else:
            print(f"Không tìm thấy file: {file_path}")

if __name__ == "__main__":
    main()
