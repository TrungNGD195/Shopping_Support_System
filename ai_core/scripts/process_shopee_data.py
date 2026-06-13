import pandas as pd
import re
import os

def extract_product_id(url):
    if pd.isna(url):
        return ""
    # Tìm chuỗi số cuối cùng trong link Shopee sau dấu chấm (VD: -i.55771655.3691999676 -> 3691999676)
    match = re.search(r'-i\.\d+\.(\d+)', str(url))
    if match:
        return match.group(1)
    return ""

def process_and_merge():
    print("Đang đọc file Excel mới...")
    df_new = pd.read_excel('Shopee_Reviews_3h34 (1).xlsx')
    
    # Chuyển đổi format
    print("Đang chuẩn hóa format...")
    df_clean = pd.DataFrame()
    df_clean['platform'] = ['shopee'] * len(df_new)
    df_clean['product_id'] = df_new['Link Sản Phẩm'].apply(extract_product_id)
    df_clean['rating'] = df_new['Đánh giá']
    df_clean['comment'] = df_new['Nội dung']
    
    # Thêm các cột rỗng cho nhãn ABSA (để khớp format cũ)
    for col in ['Quality', 'Price', 'Delivery', 'Service']:
        df_clean[col] = ''
        
    # Lọc bỏ dòng không có bình luận
    df_clean = df_clean.dropna(subset=['comment'])
    
    # Chia thành Khen và Chê
    df_pos_new = df_clean[df_clean['rating'] >= 4]
    df_neg_new = df_clean[df_clean['rating'] <= 3]
    
    # Ghép vào file cũ
    pos_path = os.path.join("data", "positive_reviews.csv")
    neg_path = os.path.join("data", "negative_reviews.csv")
    
    if os.path.exists(pos_path):
        df_pos_old = pd.read_csv(pos_path)
        df_pos_combined = pd.concat([df_pos_old, df_pos_new], ignore_index=True)
        df_pos_combined.to_csv(pos_path, index=False)
        print(f"Đã bổ sung {len(df_pos_new)} bình luận KHEN vào data/positive_reviews.csv")
        
    if os.path.exists(neg_path):
        df_neg_old = pd.read_csv(neg_path)
        df_neg_combined = pd.concat([df_neg_old, df_neg_new], ignore_index=True)
        df_neg_combined.to_csv(neg_path, index=False)
        print(f"Đã bổ sung {len(df_neg_new)} bình luận CHÊ vào data/negative_reviews.csv")

if __name__ == "__main__":
    process_and_merge()
