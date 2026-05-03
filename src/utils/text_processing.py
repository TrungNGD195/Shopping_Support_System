import re
import unicodedata
from underthesea import word_tokenize

TEENCODE_DICT = {
    "k": "không", "ko": "không", "kh": "không", "khong": "không", "hok": "không",
    "sp": "sản phẩm", "san pham": "sản phẩm",
    "dc": "được", "đc": "được", "dk": "được",
    "bt": "bình thường", 
    "nt": "nhắn tin", "rep": "trả lời", "ib": "nhắn tin",
    "auth": "chính hãng", "fake": "hàng giả",
    "shop": "cửa hàng", "sóp": "cửa hàng",
    "đẹp": "đẹp", "dep": "đẹp",
    "vs": "với",
    "chất": "chất lượng", "cl": "chất lượng",
    "ship": "giao hàng", "shipper": "người giao hàng",
    "vler": "rất", "lun": "luôn", "lunnn": "luôn"
}

# 2. Danh sách Stopwords
STOPWORDS = set([
    "thì", "là", "mà", "rằng", "thế", "này", "kia", "nọ", "vậy", 
    "nhé", "nha", "ạ", "ơi", "hả", "chứ", "đi"
])

def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = unicodedata.normalize('NFC', text)
    
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    
    text = re.sub(r'([a-zđăâêôơư])\1+', r'\1', text)
    
    text = re.sub(r'[^\w\sđăâêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]', ' ', text)
    
    words = text.split()
    cleaned_words = []
    for word in words:
        # Dịch teencode trước
        word = TEENCODE_DICT.get(word, word)
        # Nếu từ đó KHÔNG nằm trong danh sách Stopwords thì mới lấy
        if word not in STOPWORDS:
            cleaned_words.append(word)
            
    text = " ".join(cleaned_words)
    
    # Bước 6: Gom nhiều khoảng trắng thành 1
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Bước 7: Tách từ tiếng Việt bằng Underthesea (Ghép từ bằng dấu _)
    text = word_tokenize(text, format="text")
    
    return text

# DÒNG CHẠY THỬ NGHIỆM
if __name__ == "__main__":
    # Câu comment chứa đầy đủ: teencode, chữ lặp, từ vô nghĩa (này, nha, ơi, thì), email, link, icon
    test_comment = "Áo này đẹppppppp lắm nhaaaaa sóp ơi 😂, giá rẻ vler lunnnn mà giao hàng thì quá nhanhhhh!!! liên hệ nguyen.a@gmail.com hoặc http://linkspam.com nhé"
    
    print("--- TRƯỚC KHI LỌC ---")
    print(test_comment)
    print("\n--- SAU KHI LỌC ---")
    print(clean_text(test_comment))