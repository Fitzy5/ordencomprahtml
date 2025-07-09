import os
import fitz  # PyMuPDF
import tkinter as tk
from tkinter import messagebox
import logging

# Set up logging (same as in final.py)
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_pdf_content(pdf_path):
    """Print the text content of a PDF file."""
    if not os.path.isfile(pdf_path) or not pdf_path.lower().endswith('.pdf'):
        logging.error(f"Invalid PDF file: {pdf_path}")
        messagebox.showerror("Error", f"Invalid PDF file: {pdf_path}")
        return
    
    try:
        # Open the PDF document
        doc = fitz.open(pdf_path)
        print(f"Processing PDF: {pdf_path}")
        logging.info(f"Processing PDF: {pdf_path}")
        
        # Extract and print text from each page
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:
                print(f"\n--- Page {page_num} ---")
                print(text)
                logging.info(f"Extracted text from page {page_num} of {pdf_path}")
            else:
                print(f"\n--- Page {page_num} --- (No text content)")
                logging.warning(f"No text content on page {page_num} of {pdf_path}")
        
        doc.close()
        messagebox.showinfo("Success", f"Printed text content of {pdf_path}")
        logging.info(f"Successfully printed text content of {pdf_path}")
    
    except Exception as e:
        logging.error(f"Failed to process PDF {pdf_path}: {e}")
        messagebox.showerror("Error", f"Failed to process PDF {pdf_path}: {e}")

# Example usage: Replace 'sample.pdf' with your PDF path
if __name__ == "__main__":
    pdf_path = "sample.pdf"  # Update with your PDF path
    print_pdf_content(pdf_path)