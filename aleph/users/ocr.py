import pytesseract
from PIL import Image


def perform_ocr(image_file):
    try:
        ocr_text = pytesseract.image_to_string(Image.open(image_file.path))
        return ocr_text
    except Exception as e:
        print("OCR failed:", e)
        return None