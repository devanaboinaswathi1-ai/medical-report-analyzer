from PIL import Image, ImageDraw, ImageFont

# Create a blank white image
img = Image.new('RGB', (800, 600), color=(255, 255, 255))
d = ImageDraw.Draw(img)

# Ensure text is black
text_color = (0, 0, 0)

# Sample medical report text
medical_text = """
MEDICAL LABORATORY REPORT
=========================
Patient Name: John Smith
Date: March 7, 2026
DOB: 01/15/1980

TEST RESULTS
-------------------------
Hemoglobin: 14.2 g/dL   (Normal: 13.5-17.5 g/dL)
WBC Count:  6.5 x10^3/uL (Normal: 4.5-11.0 x10^3/uL)
Platelets:  250 x10^3/uL (Normal: 150-450 x10^3/uL)
RBC Count:  4.8 x10^6/uL (Normal: 4.3-5.9 x10^6/uL)

Assessment: All parameters are within normal limits.
"""

# Draw the text on the image
d.text((50, 50), medical_text, fill=text_color)
img.save('../frontend/real_text_sample.png')
print('Image generated successfully.')
