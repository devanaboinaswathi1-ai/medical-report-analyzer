from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
image = Image.open(r'C:\Users\Lenovo\.gemini\antigravity\brain\6864c5db-04db-43da-8c93-5953e0dee824\sample_report_1772880243571.png')
text = pytesseract.image_to_string(image)
print(f'Extracted Text Length: {len(text)}')
print(text)
