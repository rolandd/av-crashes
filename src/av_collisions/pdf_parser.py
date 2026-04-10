import fitz  # PyMuPDF
import requests
import io
import os
from typing import Tuple, Optional
import logging

def download_pdf(url: str) -> bytes:
    """Downloads a PDF from a URL."""
    logging.info(f"Downloading PDF: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content

def extract_section_5(pdf_bytes: bytes) -> Tuple[Optional[bytes], str]:
    """
    Parses the PDF to extract an image and text from SECTION 5.
    Returns a tuple of (image_bytes, description_text).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    description_text = ""
    image_bytes = None

    # Search for SECTION 5 header
    # Usually it's "SECTION 5 — ACCIDENT DETAILS – DESCRIPTION"
    header_text = "SECTION 5"
    found_page = -1
    header_rect = None

    for page_num in range(len(doc)):
        page = doc[page_num]
        rects = page.search_for(header_text)
        if rects:
            found_page = page_num
            header_rect = rects[0]
            break

    if found_page != -1:
        page = doc[found_page]
        # Search for SECTION 6 to find the end of Section 5
        next_section_text = "SECTION 6"
        next_rects = page.search_for(next_section_text)
        
        # Define the area to crop
        page_rect = page.rect
        top = header_rect.y1 + 5 # Start just below the header
        bottom = next_rects[0].y0 - 5 if next_rects else page_rect.y1 # End before Section 6 or at page end
        
        crop_rect = fitz.Rect(page_rect.x0, top, page_rect.x1, bottom)
        
        # Extract text from this area
        description_text = page.get_text("text", clip=crop_rect).strip()
        
        # Render the area to an image
        # Higher zoom for better quality (2.0 = 2x scale)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=crop_rect)
        image_bytes = pix.tobytes("png")

    doc.close()
    return image_bytes, description_text

def save_output(image_bytes: bytes, description: str, filename_base: str, 
                image_dir: str = "data/images", metadata_dir: str = "data/metadata") -> str:
    """Saves the extracted image and description to disk."""
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)

    image_path = os.path.join(image_dir, f"{filename_base}.png")
    with open(image_path, "wb") as f:
        f.write(image_bytes)
        
    metadata_path = os.path.join(metadata_dir, f"{filename_base}.json")
    import json
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({"description": description, "filename": f"{filename_base}.png"}, f, indent=2)
    
    return image_path
