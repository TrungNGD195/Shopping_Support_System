import pandas as pd
import os
from sklearn.model_selection import train_test_split

def main():
    data_dir = r"d:\Shopping_Support_System\data"
    neg_file = os.path.join(data_dir, "auto_labeled_cleaned_negative_reviews.csv")
    pos_file = os.path.join(data_dir, "auto_labeled_cleaned_positive_reviews.csv")
    
    # Đọc 2 file
    df_neg = pd.read_csv(neg_file)
    df_pos = pd.read_csv(pos_file)
    
    # Gộp lại thành 1 dataset chung
    df_full = pd.concat([df_neg, df_pos], ignore_index=True)
    
    # Đảo lộn ngẫu nhiên (shuffle) toàn bộ data
    df_full = df_full.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Chọn các cột cần thiết cho việc train model
    columns_to_keep = ['cleaned_comment', 'Quality', 'Price', 'Delivery', 'Service']
    df_full = df_full[columns_to_keep]
    
    # Chia tập Train (80%), Val (10%), Test (10%)
    train_df, temp_df = train_test_split(df_full, test_size=0.2, random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)
    
    # Lưu ra file
    dataset_dir = os.path.join(data_dir, "dataset_split")
    os.makedirs(dataset_dir, exist_ok=True)
    
    train_df.to_csv(os.path.join(dataset_dir, "train.csv"), index=False, encoding='utf-8-sig')
    val_df.to_csv(os.path.join(dataset_dir, "val.csv"), index=False, encoding='utf-8-sig')
    test_df.to_csv(os.path.join(dataset_dir, "test.csv"), index=False, encoding='utf-8-sig')
    
    print(f"Đã tạo thư mục: {dataset_dir}")
    print(f"Tổng số mẫu: {len(df_full)}")
    print(f"  - Train: {len(train_df)} mẫu")
    print(f"  - Val:   {len(val_df)} mẫu")
    print(f"  - Test:  {len(test_df)} mẫu")

if __name__ == "__main__":
    main()
