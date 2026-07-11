import streamlit as st
import requests
import json

# Cấu hình giao diện
st.set_page_config(page_title="Hệ Thống Trích Xuất BCTC", layout="wide")
st.title("Hệ Thống Trích Xuất BCTC Thông Minh 🚀")
st.markdown("Hệ thống tự động băm nhỏ file PDF và sử dụng **Qwen3-VL** để bóc tách dữ liệu.")

# Khu vực kéo thả file
uploaded_file = st.file_uploader("Kéo thả file PDF Báo cáo tài chính (Tài liệu Scan) vào đây", type=['pdf'])

if uploaded_file is not None:
    if st.button("Bắt đầu bóc tách", type="primary"):
        with st.spinner("Đang gửi tài liệu và xử lý qua AI. Quá trình này có thể mất vài phút với file dài..."):
            try:
                # Gửi file tới Backend FastAPI (cổng 8080)
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post("[http://127.0.0.1:8080/api/extract](http://127.0.0.1:8080/api/extract)", files=files)
                
                if response.status_code == 200:
                    res_data = response.json()
                    if res_data["status"] == "success":
                        st.success(f"Hoàn tất xử lý {res_data['total_pages']} trang!")
                        
                        # Hiển thị kết quả của từng lô
                        for batch in res_data["results"]:
                            with st.expander(f"Kết quả trích xuất Trang {batch['batch_start']} - {batch['batch_end']}", expanded=True):
                                st.json(batch["data"])
                    else:
                        st.error(f"Lỗi hệ thống từ Backend: {res_data.get('message')}")
                else:
                    st.error(f"Lỗi kết nối (Status Code: {response.status_code}). Backend trả về lỗi.")
                    
            except Exception as e:
                st.error(f"Không thể kết nối tới Backend. Hãy chắc chắn bạn đã chạy file backend_main.py ở cổng 8080. Chi tiết lỗi: {e}")