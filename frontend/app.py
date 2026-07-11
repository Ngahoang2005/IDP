import streamlit as st
import requests

st.set_page_config(page_title="Hỏi đáp BCTC", layout="wide")
st.title("Hệ Thống Đọc và Hỏi Đáp BCTC 🚀")

user_query = st.text_input(
    "Bạn muốn hỏi gì về tài liệu này?", 
    value="Hãy bóc tách các dữ liệu quan trọng trong tài liệu này thành định dạng JSON."
)

# SỬA LẠI: Thêm các định dạng ảnh và cho phép chọn nhiều file cùng lúc
uploaded_files = st.file_uploader(
    "Kéo thả các file PDF hoặc Ảnh (Scan) vào đây (Có thể chọn nhiều file)", 
    type=['pdf', 'png', 'jpg', 'jpeg'],
    accept_multiple_files=True
)

# Kiểm tra xem có file nào được upload không
if uploaded_files:
    if st.button("Gửi tài liệu và câu hỏi", type="primary"):
        with st.spinner(f"Đang đọc {len(uploaded_files)} file tài liệu và suy nghĩ câu trả lời..."):
            try:
                # Đóng gói toàn bộ các file thành một danh sách để gửi đi
                files_data = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                data = {"query": user_query}
                
                response = requests.post("http://127.0.0.1:8080/api/extract", files=files_data, data=data)
                
                if response.status_code == 200:
                    res_data = response.json()
                    if res_data["status"] == "success":
                        st.success(f"Đã xử lý xong tổng cộng {res_data['total_pages']} trang dữ liệu!")
                        
                        for batch in res_data["results"]:
                            with st.expander(f"Trả lời cho Trang {batch['batch_start']} - {batch['batch_end']}", expanded=True):
                                st.write(batch["answer"])
                    else:
                        st.error(f"Lỗi hệ thống: {res_data.get('message')}")
                else:
                    st.error(f"Lỗi kết nối (Code: {response.status_code}).")
                    
            except Exception as e:
                st.error(f"Không thể kết nối tới Backend. Chi tiết lỗi: {e}")