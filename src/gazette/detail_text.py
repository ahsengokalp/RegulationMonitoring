from __future__ import annotations

import io
import re
import requests
from bs4 import BeautifulSoup

try:
    import fitz  # pymupdf
except Exception:  # pragma: no cover - optional dependency
    fitz = None  # type: ignore[assignment]

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None  # type: ignore[assignment]

try:
    from PIL import Image
    import pytesseract
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore[assignment]
    pytesseract = None  # type: ignore[assignment]


def fetch_detail_text(session: requests.Session, url: str, timeout_s: int = 40) -> str:
    if url.lower().endswith(".pdf"):
        pdf_bytes = _download_bytes(session, url, timeout_s)
        text = _extract_pdf_text_with_ocr(pdf_bytes, dpi=250)
        if _looks_like_real_text(text):
            return text
        if PdfReader is not None:
            text = _extract_pdf_text_with_pypdf(pdf_bytes)
        return (text or "").strip()

    html = _download_text(session, url, timeout_s)
    return _extract_text_from_html(html)


def _download_bytes(session: requests.Session, url: str, timeout_s: int) -> bytes:
    r = session.get(url, timeout=timeout_s)
    r.raise_for_status()
    return r.content


def _download_text(session: requests.Session, url: str, timeout_s: int) -> str:
    r = session.get(url, timeout=timeout_s)
    r.raise_for_status()
    return r.text


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one("#html-content")
    if content:
        return content.get_text("\n", strip=True)
    return soup.get_text("\n", strip=True)


def _extract_pdf_text_with_ocr(pdf_bytes: bytes, dpi: int = 250) -> str:
    if fitz is None:
        return ""

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # 1) Önce metin dene (hızlı)
    parts = []
    for page in doc:
        t = (page.get_text("text") or "").strip()
        if t:
            parts.append(t)
    text = "\n\n".join(parts).strip()
    if _looks_like_real_text(text):
        return text

    if Image is None or pytesseract is None:
        return text

    # 2) Metin yoksa OCR (sağlam render)
    ocr_parts = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)  # render
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        ocr = (pytesseract.image_to_string(img, lang="tur") or "").strip()
        if ocr:
            ocr_parts.append(ocr)

    return "\n\n".join(ocr_parts).strip()


def _extract_pdf_text_with_pypdf(pdf_bytes: bytes) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    parts = []
    for page in reader.pages:
        t = (page.extract_text() or "").strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts).strip()


def _looks_like_real_text(text: str) -> bool:
    text = (text or "").strip()
    if len(text) < 80:
        return False
    letters = sum(ch.isalpha() for ch in text)
    ratio = letters / max(len(text), 1)
    words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    return ratio > 0.25 and len(words) >= 12
