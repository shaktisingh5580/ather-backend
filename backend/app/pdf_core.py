# backend/app/engine/pdf_core.py
import fitz  # PyMuPDF
import io
from PIL import Image

def analyze_pdf_structure(pdf_bytes: bytes):
    """
    Scans the PDF and returns a map of all images.
    Returns: JSON list of images with Page # and Layout Info.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    image_report = []

    for page_index, page in enumerate(doc):
        # 1. Get all images on the page
        image_list = page.get_images(full=True)
        
        for img in image_list:
            xref = img[0]  # The unique ID of the image object
            
            # 2. Get exact location on the page (BBox)
            # A single xref might appear multiple times (e.g., a logo)
            rects = page.get_image_rects(xref)
            
            for rect in rects:
                image_report.append({
                    "page": page_index + 1,
                    "xref": xref,
                    "width": rect.width,
                    "height": rect.height,
                    "x": rect.x0,
                    "y": rect.y0,
                    "desc": f"Image (ID: {xref}) on Page {page_index + 1}"
                })
                
    return image_report

def extract_image_by_xref(pdf_bytes: bytes, xref: int):
    """
    Extracts a specific image from the PDF so we can send it to AI.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    base_image = doc.extract_image(xref)
    return base_image["image"]  # Returns bytes

def replace_image_in_pdf(pdf_bytes: bytes, target_xref: int, new_image_bytes: bytes):
    """
    THE BULK SWAPPER:
    Replaces the image stream at 'target_xref'.
    If this xref is used on Page 1, 50, and 999, ALL of them update instantly.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # 1. Resize new image to match the old one (Crucial for layout)
    # We grab the old image just to check its dimensions/format
    old_img = doc.extract_image(target_xref)
    
    # 2. Perform the surgical swap
    # This updates the binary stream inside the PDF container
    doc.update_stream(target_xref, new_image_bytes)
    
    # 3. Save to a new memory buffer
    out_buffer = io.BytesIO()
    doc.save(out_buffer)
    return out_buffer.getvalue()