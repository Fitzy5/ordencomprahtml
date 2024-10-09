import re
import fitz  # PyMuPDF

# Specify the path to the PDF file
file_path = "COV0000015024 EMP CONST MAHUIDA LTDA EIFS 060824.pdf"

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf_document:
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
    return text

# Regex pattern to extract quotation number
pattern = r'Nro:\s*0*(\d{4,})'

# Extract text from PDF
text = extract_text_from_pdf(file_path)

# Search for quotation number
match = re.search(pattern, text)
if match:
    quotation_number = match.group(1)
    print(f"Quotation number found: {quotation_number}")
else:
    print("No quotation number found.")
