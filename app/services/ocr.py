from PIL import Image
import pytesseract
from app.utils.logging import setup_logging

logger = setup_logging()

def extract_text(file_path: str) -> str:
    try:
        # TODO: Add PDF-to-image conversion for PDF files using pdf2image
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        logger.info(f"Extracted text from {file_path}")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        raise