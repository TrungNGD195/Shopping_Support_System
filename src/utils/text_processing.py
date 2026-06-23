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
        word = TEENCODE_DICT.get(word, word)
        if word not in STOPWORDS:
            cleaned_words.append(word)
            
    text = " ".join(cleaned_words)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    text = word_tokenize(text, format="text")
    
    return text

if __name__ == "__main__":
    test_comment = "Áo này đẹppppppp lắm nhaaaaa sóp ơi 😂, giá rẻ vler lunnnn mà giao hàng thì quá nhanhhhh!!! liên hệ nguyen.a@gmail.com hoặc http://linkspam.com nhé"
    
    print("--- TRƯỚC KHI LỌC ---")
    print(test_comment)
    print("\n--- SAU KHI LỌC ---")
    print(clean_text(test_comment))