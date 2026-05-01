import streamlit as st
import time

# Cấu hình cơ bản cho trang Web
st.set_page_config(
    page_title="Shopping Support System", 
    page_icon="🛒", 
    layout="centered"
)

# Giao diện chính
st.title("🛒 Shopping Support System")
st.markdown("""
Hệ thống AI tự động phân tích hàng ngàn bình luận, giúp bạn biết chính xác **Chất lượng, Giá cả, Giao hàng và Dịch vụ** của sản phẩm trước khi chốt đơn!
""")
st.markdown("---")

# Ô nhập Link
url_input = st.text_input(
    "🔗 Dán link sản phẩm (Shopee/Tiki/Lazada) vào đây:", 
    placeholder="https://shopee.vn/ao-thun-nam-..."
)

# Nút bấm kích hoạt
if st.button("🚀 Phân tích ngay", use_container_width=True, type="primary"):
    if url_input.strip() == "":
        st.warning("⚠️ Cảnh báo: Bạn chưa nhập link sản phẩm kìa!")
    else:
        # Cất URL vào "túi" Session State để mang sang trang báo cáo
        st.session_state['product_url'] = url_input
        
        # Tạo hiệu ứng chờ cho ngầu
        with st.spinner("⏳ Đang cào dữ liệu và phân tích comment... Vui lòng đợi trong giây lát!"):
            time.sleep(1.5) # Giả vờ load 1.5 giây
            
            # Xử lý xong thì chuyển hướng sang Trang Dashboard
            st.switch_page("pages/1_phan_tich.py")