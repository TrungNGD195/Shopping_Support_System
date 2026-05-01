import streamlit as st
import pandas as pd
import plotly.express as px
import time
import sys
import os

# --- XỬ LÝ ĐƯỜNG DẪN ĐỂ IMPORT ĐƯỢC CODE TỪ THƯ MỤC KHÁC ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.inference import ABSAPredictor

st.set_page_config(page_title="Kết quả Phân tích", page_icon="📊", layout="wide")

# ==========================================
# 1. NẠP MÔ HÌNH AI (CHỈ NẠP 1 LẦN DUY NHẤT)
# ==========================================
@st.cache_resource(show_spinner="🧠 Đang khởi động lõi AI (chỉ tốn lần đầu tiên)...")
def load_ai_model():
    return ABSAPredictor()

ai_station = load_ai_model()

# ==========================================
# 2. XỬ LÝ DỮ LIỆU TỪ TRANG CHỦ
# ==========================================
url = st.session_state.get('product_url', None)

if not url:
    st.warning("⚠️ Vui lòng quay lại Trang chủ và nhập Link sản phẩm!")
    st.stop()

st.title("📊 Kết quả Phân tích Sản phẩm")
st.markdown(f"**🔗 Link sản phẩm:** [{url[:60]}...]({url})")
st.markdown("---")

# ==========================================
# 3. CHẠY AI & TỔNG HỢP SỐ LIỆU (AGGREGATION)
# ==========================================
# Tạm thời dùng 5 câu comment giả lập (Thay vì gọi Crawler thật của Khánh)
sample_comments = [
    "Áo đẹp, vải mát mẻ nhưng mà giao hàng chậm quá shop ơi.",
    "Hàng fake, mỏng dính, giá đắt cắt cổ, nhắn tin đéo thèm rep!",
    "Chất lượng bình thường, tạm ổn trong tầm giá 50k.",
    "Giao siêu tốc, đóng gói đẹp, 10 điểm dịch vụ.",
    "Mặc được 1 lần xù lông hết, thất vọng thực sự."
]

# Tạo bộ khung rỗng để AI điền số liệu vào
result_data = {
    "overview": {"total_analyzed_comments": len(sample_comments), "final_verdict": "Chưa có đánh giá"},
    "aspects": {
        "Quality": {"stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, "highlights": {"positive": [], "negative": []}, "summary": "Chất lượng sản phẩm theo AI đánh giá..."},
        "Price":   {"stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, "highlights": {"positive": [], "negative": []}, "summary": "Mức giá so với giá trị mang lại..."},
        "Delivery":{"stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, "highlights": {"positive": [], "negative": []}, "summary": "Tốc độ và chất lượng đóng gói..."},
        "Service": {"stats": {"Khen": 0, "Bình thường": 0, "Chê": 0, "Không nhắc tới": 0}, "highlights": {"positive": [], "negative": []}, "summary": "Thái độ phản hồi của shop..."}
    }
}

# CHẠY LUỒNG AI THẬT
with st.spinner("⏳ AI đang đọc từng bình luận để phân tích..."):
    for cmt in sample_comments:
        prediction = ai_station.predict_single_comment(cmt)
        
        # Bóc tách kết quả cho từng khía cạnh
        for aspect, data in prediction["aspects"].items():
            label_text = data['text']
            
            # Quy đổi nhãn AI (có icon) thành Key chuẩn để đếm
            if "Khen" in label_text:
                result_data["aspects"][aspect]["stats"]["Khen"] += 1
                result_data["aspects"][aspect]["highlights"]["positive"].append(cmt)
            elif "Chê" in label_text:
                result_data["aspects"][aspect]["stats"]["Chê"] += 1
                result_data["aspects"][aspect]["highlights"]["negative"].append(cmt)
            elif "Bình thường" in label_text:
                result_data["aspects"][aspect]["stats"]["Bình thường"] += 1
            else:
                result_data["aspects"][aspect]["stats"]["Không nhắc tới"] += 1

# Tính toán Verdict (Khen nhiều thì cho "Đáng mua")
total_khen = sum([result_data["aspects"][asp]["stats"]["Khen"] for asp in result_data["aspects"]])
total_che = sum([result_data["aspects"][asp]["stats"]["Chê"] for asp in result_data["aspects"]])
result_data["overview"]["final_verdict"] = "🟢 Rất Đáng Mua" if total_khen > total_che else "🔴 Cần Cân Nhắc"

# ==========================================
# 4. VẼ GIAO DIỆN OVERVIEW (Giữ nguyên như cũ)
# ==========================================
col1, col2 = st.columns(2)
with col1:
    st.success(f"**Đánh giá tổng quan:** {result_data['overview']['final_verdict']}")
with col2:
    st.info(f"**Tổng số bình luận đã phân tích:** {result_data['overview']['total_analyzed_comments']}")

st.write("### 🔍 Phân tích chi tiết theo 4 khía cạnh")

# ==========================================
# 5. VẼ GIAO DIỆN 4 TABS 
# ==========================================
tabs = st.tabs(["👕 Chất lượng", "💰 Giá cả", "🚚 Giao hàng", "🎧 Dịch vụ"])
aspect_keys = ["Quality", "Price", "Delivery", "Service"]

for i, tab in enumerate(tabs):
    with tab:
        aspect_name = aspect_keys[i]
        data = result_data["aspects"][aspect_name]
        
        st.markdown(f"**👉 AI Tóm tắt:** {data['summary']}")
        
        col_chart, col_text = st.columns([1, 1])
        
        with col_chart:
            # Lọc bỏ thuộc tính "Không nhắc tới" cho biểu đồ đỡ rác
            plot_stats = {k: v for k, v in data["stats"].items() if k != "Không nhắc tới" and v > 0}
            
            if plot_stats:
                df = pd.DataFrame({"Cảm xúc": list(plot_stats.keys()), "Số lượng": list(plot_stats.values())})
                fig = px.pie(df, values="Số lượng", names="Cảm xúc", 
                             color="Cảm xúc",
                             color_discrete_map={"Khen": "#28a745", "Bình thường": "#ffc107", "Chê": "#dc3545"},
                             hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("👻 *Chưa có ai nhắc đến khía cạnh này.*")
            
        with col_text:
            st.write("#### 💬 Bằng chứng từ khách hàng")
            with st.expander("✅ Xem bình luận Khen"):
                for cmt in set(data["highlights"]["positive"]): # Dùng set() để lọc trùng lặp
                    st.write(f"- *{cmt}*")
            with st.expander("❌ Xem bình luận Chê"):
                for cmt in set(data["highlights"]["negative"]):
                    st.write(f"- *{cmt}*")