import streamlit as st
import requests

st.set_page_config(page_title="Hỏi đáp BCTC", layout="wide")
st.title("Hệ Thống Đọc và Hỏi Đáp BCTC 🚀")

# Thêm ô nhập câu hỏi
user_query = st.text_input(
    "Bạn muốn hỏi gì về tài liệu này?", 
    value="Hãy bóc tách các dữ liệu quan trọng trong trang này thành định dạng JSON."
)

uploaded_file = st.file_uploader("Kéo thả file PDF (Scan) vào đây", type=['pdf'])

if uploaded_file is not None:
    if st.button("Gửi câu hỏi", type="primary"):
        with st.spinner("Đang đọc tài liệu và suy nghĩ câu trả lời..."):
            try:
                # Gửi cả file và câu hỏi (data) sang Backend
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                data = {"query": user_query}
                
                # Đã sửa lại đúng định dạng URL như bạn gặp lỗi lúc nãy
                response = requests.post("http://127.0.0.1:8080/api/extract", files=files, data=data)
                
                if response.status_code == 200:
                    res_data = response.json()
                    if res_data["status"] == "success":
                        st.success(f"Đã đọc xong {res_data['total_pages']} trang!")
                        
                        for batch in res_data["results"]:
                            with st.expander(f"Trả lời cho Trang {batch['batch_start']} - {batch['batch_end']}", expanded=True):
                                st.write(batch["answer"])
                    else:
                        st.error(f"Lỗi: {res_data.get('message')}")
                else:
                    st.error(f"Lỗi kết nối (Code: {response.status_code}).")
                    
            except Exception as e:
                st.error(f"Không thể kết nối tới Backend. Chi tiết lỗi: {e}")