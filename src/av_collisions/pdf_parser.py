import fitz  # type: ignore[import-untyped]
import requests
import os
import json
from typing import Tuple, Optional, Dict, Any
import logging


def download_pdf(url: str) -> bytes:
    """Downloads a PDF from a URL."""
    logging.info(f"Downloading PDF: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def extract_section_5(
    pdf_bytes: bytes,
) -> Tuple[Optional[bytes], int, int, str, Dict[str, Any]]:
    """
    Parses the PDF to extract an image and text from SECTION 5.
    Also extracts checkbox values for Autonomous and Conventional modes.
    Returns a tuple of (image_bytes, width, height, description_text, extra_metadata).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    description_text = ""
    image_bytes = None
    width, height = 0, 0
    extra_metadata = {}

    # Search for SECTION 5 header
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

        # 1. Extract Checkbox Values
        # Pre-initialize with False
        extra_metadata["autonomous_mode"] = False
        extra_metadata["conventional_mode"] = False

        for widget in page.widgets():
            field_name = widget.field_name
            field_value = widget.field_value

            # If field_value is set and not /Off, it is checked
            is_checked = bool(field_value and field_value != "/Off")

            label = (widget.field_label or "").lower()
            name = (field_name or "").lower()

            if "autonomous mode" in label or "autonomous_mode" in name:
                extra_metadata["autonomous_mode"] = is_checked
            elif "conventional mode" in label or "conventional_mode" in name:
                extra_metadata["conventional_mode"] = is_checked

        # 2. Define the area to crop
        assert header_rect is not None
        top = header_rect.y1 + 5

        # Find the "Additional information attached" text to use as the cutoff
        cutoff_text = "Additional information attached"
        cutoff_rects = page.search_for(cutoff_text)

        valid_cutoff = None
        for r in cutoff_rects:
            if r.y0 > top:
                valid_cutoff = r
                break

        if valid_cutoff:
            # Cut off just ABOVE the checkbox/text for "Additional information attached"
            bottom = valid_cutoff.y0 - 2
        else:
            # Fallback to SECTION 6 if not found BELOW the header
            next_section_text = "SECTION 6"
            next_rects = page.search_for(next_section_text)
            valid_next = None
            for r in next_rects:
                if r.y0 > top:
                    valid_next = r
                    break

            if valid_next:
                bottom = valid_next.y0 - 5
            else:
                bottom = page.rect.y1

        if bottom <= top:
            bottom = page.rect.y1

        page_rect = page.rect
        initial_crop = fitz.Rect(page_rect.x0, top, page_rect.x1, bottom)

        # 3. Find the actual text bounding box within the initial crop area
        # This prevents large areas of whitespace if the description is short.
        text_rect = fitz.Rect()
        blocks = page.get_text("dict", clip=initial_crop)["blocks"]
        for b in blocks:
            if b["type"] == 0:  # text block
                text_rect.include_rect(b["bbox"])

        if not text_rect.is_empty:
            # Add some healthy padding (20pts horizontal, 10pts vertical)
            # but keep it within the page boundaries and the initial crop
            final_crop = fitz.Rect(
                max(page_rect.x0, text_rect.x0 - 20),
                max(top, text_rect.y0 - 10),
                min(page_rect.x1, text_rect.x1 + 20),
                min(bottom, text_rect.y1 + 10),
            )
        else:
            final_crop = initial_crop

        # Extract text from the initial area to ensure we don't miss anything
        description_text = page.get_text("text", clip=initial_crop).strip()

        # Render the area to an image using the refined crop
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=final_crop)
        image_bytes = pix.tobytes("png")
        width, height = pix.width, pix.height

    doc.close()
    return image_bytes, width, height, description_text, extra_metadata


def save_output(
    image_bytes: bytes,
    description: str,
    slug: str,
    url: str,
    extra_metadata: Dict[str, Any],
    output_dir: str = ".",
) -> str:
    """Saves the extracted image and description to disk."""
    os.makedirs(output_dir, exist_ok=True)

    image_path = os.path.join(output_dir, f"{slug}.png")
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    metadata_path = os.path.join(output_dir, f"{slug}.json")

    full_metadata = {
        "description": description,
        "filename": f"{slug}.png",
        "original_url": url,
        **extra_metadata,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(full_metadata, f, indent=2)

    return image_path
