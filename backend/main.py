import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from PIL import Image # Thêm thư viện xử lý ảnh
from openai import OpenAI
from typing import List # Thêm typing

app = FastAPI(title="Qwen3-VL BCTC API")

client = OpenAI(
    api_key="EMPTY",
    base_url="http://127.0.0.1:8000/v1"
)

BATCH_SIZE = 3  

def process_bctc_batch(base64_batch, user_query):
    content = []
    for img_b64 in base64_batch:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
        })
    
    content.append({
        "type": "text", 
        "text": user_query
    })

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-VL-2B-Instruct",
            messages=[{"role": "user", "content": content}],
            max_tokens=2048,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# SỬA LẠI HÀM NÀY: Nhận danh sách nhiều file (List[UploadFile])
@app.post("/api/extract")
async def extract_bctc(files: List[UploadFile] = File(...), query: str = Form(...)):
    try:
        base64_images = []
        
        # Lặp qua tất cả các file người dùng tải lên
        for file in files:
            file_bytes = await file.read()
            
            # Phân loại 1: Nếu là file PDF
            if file.filename.lower().endswith(".pdf"):
                images = convert_from_bytes(file_bytes, dpi=200)
                for img in images:
                    buffered = BytesIO()
                    img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    base64_images.append(img_str)
                    
            # Phân loại 2: Nếu là file Ảnh (PNG, JPG, JPEG)
            elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(BytesIO(file_bytes)).convert("RGB")
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                base64_images.append(img_str)
                
            else:
                return JSONResponse(content={"status": "error", "message": f"Không hỗ trợ định dạng của file: {file.filename}"}, status_code=400)
        
        all_results = []
        total_pages = len(base64_images)
        
        # Cửa sổ trượt: Cứ lấy 3 trang một để xử lý, bất kể nó đến từ PDF hay Ảnh rời
        for i in range(0, total_pages, BATCH_SIZE):
            batch = base64_images[i : i + BATCH_SIZE]
            result_text = process_bctc_batch(batch, query)
            
            all_results.append({
                "batch_start": i + 1,
                "batch_end": min(i+BATCH_SIZE, total_pages),
                "answer": result_text
            })
            
        return JSONResponse(content={"status": "success", "total_pages": total_pages, "results": all_results})

    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)