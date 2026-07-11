import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from openai import OpenAI
import json

app = FastAPI(title="Qwen3-VL BCTC API")

# Cấu hình kết nối tới vLLM (Đảm bảo vLLM đang chạy ở port 8000)
client = OpenAI(
    api_key="EMPTY",
    base_url="http://127.0.0.1:8000/v1"
)

# Giới hạn số trang mỗi lần đọc để Card 4090 không bị Out of Memory
BATCH_SIZE = 3  

def process_bctc_batch(base64_batch):
    content = []
    for img_b64 in base64_batch:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
        })
    
    # Ép mô hình trả về JSON
    content.append({
        "type": "text", 
        "text": "Bạn là chuyên gia bóc tách tài liệu kế toán. Hãy đọc các trang Báo cáo tài chính này và trích xuất dữ liệu thành định dạng JSON. Chỉ trả về JSON thuần túy, không giải thích gì thêm."
    })

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-VL-2B-Instruct",
            messages=[{"role": "user", "content": content}],
            max_tokens=2048,
            temperature=0.1 # Nhiệt độ thấp để con số chính xác, không bị ảo giác
        )
        # Loại bỏ các tag markdown ```json nếu có để file sạch
        raw_text = response.choices[0].message.content
        clean_text = raw_text.replace("```json\n", "").replace("```", "").strip()
        return clean_text
    except Exception as e:
        return str(e)

@app.post("/api/extract")
async def extract_bctc(file: UploadFile = File(...)):
    try:
        # 1. Đọc file PDF từ request
        pdf_bytes = await file.read()
        
        # 2. Convert PDF sang danh sách ảnh (dpi 200 để rõ số liệu)
        images = convert_from_bytes(pdf_bytes, dpi=200)
        
        # 3. Chuyển ảnh sang Base64 để gửi qua API
        base64_images = []
        for img in images:
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_images.append(img_str)
        
        # 4. Xử lý theo lô (Sliding Window)
        all_results = []
        total_pages = len(base64_images)
        
        for i in range(0, total_pages, BATCH_SIZE):
            batch = base64_images[i : i + BATCH_SIZE]
            print(f"Đang xử lý lô từ trang {i+1} đến {min(i+BATCH_SIZE, total_pages)}...")
            
            result_text = process_bctc_batch(batch)
            
            # Cố gắng parse chuỗi thành JSON Object thực thụ
            try:
                parsed_json = json.loads(result_text)
            except:
                parsed_json = {"raw_text": result_text}

            all_results.append({
                "batch_start": i + 1,
                "batch_end": min(i+BATCH_SIZE, total_pages),
                "data": parsed_json
            })
            
        return JSONResponse(content={"status": "success", "total_pages": total_pages, "results": all_results})

    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)