from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.engine.pdf_core import analyze_pdf_structure, extract_image_by_xref, replace_image_in_pdf
from app.intelligence.ai_service import generate_inpainting, analyze_image_context
from dotenv import load_dotenv
import os

load_dotenv() # Load keys from .env

app = FastAPI(title="DocuGenius Free")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# Simple in-memory storage for MVP
PDF_STORE = {}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    content = await file.read()
    PDF_STORE["file"] = content
    # Return the structure (images + locations)
    return analyze_pdf_structure(content)

@app.post("/analyze_image")
async def analyze_xref(xref: int = Form(...)):
    """
    Ask OpenRouter what is inside this specific image.
    """
    if "file" not in PDF_STORE: return {"error": "No file"}
    
    img_bytes = extract_image_by_xref(PDF_STORE["file"], xref)
    description = analyze_image_context(img_bytes)
    return {"xref": xref, "description": description}

@app.post("/edit/replace")
async def edit_image(
    xref: int = Form(...), 
    prompt: str = Form(...)
):
    """
    The Core Feature: In-Place Replacement using Free APIs.
    """
    if "file" not in PDF_STORE: return {"error": "No file"}
    
    # 1. Get Original
    original_bytes = extract_image_by_xref(PDF_STORE["file"], xref)
    
    # 2. Create a "Dummy Mask" (In a real app, Frontend sends this)
    # For now, we create a white square mask (edit everything)
    from PIL import Image, ImageOps
    import io
    
    orig_img = Image.open(io.BytesIO(original_bytes))
    # Create a mask that selects the whole image for replacement
    mask = Image.new("L", orig_img.size, 255) 
    mask_buffer = io.BytesIO()
    mask.save(mask_buffer, format="PNG")
    mask_bytes = mask_buffer.getvalue()

    # 3. Generate New Image (Hugging Face)
    print(f"Painting new image for XREF {xref}...")
    new_bytes = generate_inpainting(original_bytes, mask_bytes, prompt)
    
    # 4. Surgically Replace (PyMuPDF)
    PDF_STORE["file"] = replace_image_in_pdf(PDF_STORE["file"], xref, new_bytes)
    
    return {"status": "success", "message": "Image Updated"}

@app.get("/download")
async def download():
    from fastapi.responses import Response
    return Response(
        content=PDF_STORE.get("file", b""), 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=edited.pdf"}
    )