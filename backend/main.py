import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from openai import OpenAI

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
    
    # Dùng chính câu hỏi của người dùng thay vì gắn cứng
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

@app.post("/api/extract")
async def extract_bctc(file: UploadFile = File(...), query: str = Form(...)):
    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes, dpi=200)
        
        base64_images = []
        for img in images:
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_images.append(img_str)
        
        all_results = []
        total_pages = len(base64_images)
        
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