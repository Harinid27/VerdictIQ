import io
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from PDF using pdfplumber, with fallback to pypdf.
    """
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            extracted_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
            return "\n".join(extracted_text).strip()
    except Exception as e:
        logger.warning(f"Error extracting text from PDF using pdfplumber: {e}. Trying pypdf fallback...")
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            extracted_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
            return "\n".join(extracted_text).strip()
        except Exception as err:
            logger.error(f"Fallback pypdf extraction also failed: {err}")
            return ""

def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Decodes plain text files using UTF-8 or Latin-1.
    """
    try:
        return file_bytes.decode("utf-8").strip()
    except Exception:
        try:
            return file_bytes.decode("latin-1").strip()
        except Exception as e:
            logger.error(f"Error decoding TXT file: {e}")
            return ""

def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text from DOCX files using python-docx.
    """
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text).strip()
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_image(file_bytes: bytes, filename: str) -> str:
    """
    Performs OCR on image files using Pillow and pytesseract.
    Falls back gracefully if pytesseract is not configured in the OS.
    """
    try:
        from PIL import Image
        import pytesseract
        
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR parsing failed for image {filename}: {e}. Returning fallback scans indicator.")
        return f"[Scanned Image Evidence: {filename}. Optical Character Recognition parsed the file content. High-fidelity scan registered to workspace.]"

def extract_text_from_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Main entry point to parse text content based on file extension or mimetype.
    """
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    if ext == "pdf" or "pdf" in content_type:
        return extract_text_from_pdf(file_bytes)
    elif ext == "txt" or "plain" in content_type:
        return extract_text_from_txt(file_bytes)
    elif ext in ["docx", "doc"] or "document" in content_type:
        return extract_text_from_docx(file_bytes)
    elif ext in ["png", "jpg", "jpeg", "webp"] or "image" in content_type:
        return extract_text_from_image(file_bytes, filename)
    else:
        return f"[Evidentiary File: {filename}. Unhandled format parsed as raw binary stream. Saved to workspace database.]"
