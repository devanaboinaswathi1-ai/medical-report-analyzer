from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
image = Image.open('../frontend/sample_test.png')
text = pytesseract.image_to_string(image)
print(f'Extracted Text Length: {len(text)}')
print(text)
