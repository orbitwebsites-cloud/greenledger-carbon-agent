from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
PDF_SUFFIXES = {".pdf"}

# GreenLedger runs OCR fully offline with EasyOCR. EasyOCR's detection/recognition
# weights are downloaded once from its public model repo on first use and cached
# locally (~/.EasyOCR) — no paid or gated API key is required, and every run after
# the first is 100% offline.


@lru_cache(maxsize=1)
def _reader():
    import easyocr

    return easyocr.Reader(["en"], gpu=False, verbose=False)


def ocr_image(image: Image.Image) -> str:
    array = np.array(image.convert("RGB"))
    results = _reader().readtext(array, detail=0, paragraph=True)
    return "\n".join(results)


def ocr_image_file(path: Path) -> str:
    with Image.open(path) as img:
        return ocr_image(img)


def ocr_pdf_file(path: Path, dpi: int = 300) -> str:
    """Render each page of a PDF to an image and OCR it. Uses PyMuPDF (no external
    poppler dependency), so this stays fully offline / local."""
    import fitz  # PyMuPDF

    text_parts = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            mode = "RGB" if pix.alpha == 0 else "RGBA"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
            text_parts.append(ocr_image(img))
    return "\n".join(text_parts)


def ocr_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in PDF_SUFFIXES:
        return ocr_pdf_file(path)
    if suffix in IMAGE_SUFFIXES:
        return ocr_image_file(path)
    raise ValueError(f"Unsupported file type for OCR: {path}")
