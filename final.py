#fix loader puting correlational oc numbers to old quotations































import fitz  # PyMuPDF
import re
from jinja2 import Environment, FileSystemLoader
import asyncio
from pyppeteer import launch
import tempfile
import os
from datetime import datetime
import locale
import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import csv
import math
from tkinter import messagebox  # Add this import for displaying messages
from datetime import date






# Set locale for currency formatting
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


info_ebema = {
    "vendedor": "Marcelo Arias A.",
    "direccion_proveedor": "Suc. Temuco Reyes Catolicos 01550",
    "ubicacion_proveedor": "Temuco, Region de La Araucania",
    "contacto_proveedor": "±569 74994160",
    "correo_proveedor": "marias@ebema.cl"
}

info_mct = {
    "vendedor": "Jorge boutad",
    "direccion_proveedor": "Caupolican 957",
    "ubicacion_proveedor": "Temuco, Region de La Araucania",
    "contacto_proveedor": "452210095",
    "correo_proveedor": "jboutaud@mct.cl"
}

info_adco = {
    "vendedor": "Miguel Bravo Segura",
    "direccion_proveedor": "Av. Pedro de valdivia 0682-a",
    "ubicacion_proveedor": "Temuco, Region de La Araucania",
    "contacto_proveedor": "045-2318391",
    "correo_proveedor": "mbravo@adcoltda.cl"
}

info_aislacentro = {
    "vendedor": "Jaime Esteban Varas Perez",
    "direccion_proveedor": "Camino a Coronel #KM 10 5580, Mod. 19 A, San Pedro de la Paz",
    "ubicacion_proveedor": "San Pedro de la Paz, Región del Biobío",
    "contacto_proveedor": "045-2213148",
    "correo_proveedor": "coordinador@aislacentro.cl"
}

info_aislapanel_nv = {
    "vendedor": "Claudia Bravo",
    "provider": "AISLAPANEL S.A.",
    "direccion_proveedor": "Miguel Faraday 2470 bodega 10",
    "contacto_proveedor": "+56 9 5158 6942",
    "correo_proveedor": "contacto@aislapanel.cl"
}

info_aislapanel_cv = {
    "vendedor": "Claudia Bravo",
    "provider": "AISLAPANEL S.A.",
    "direccion_proveedor": "Miguel Faraday 2470 bodega 10",
    "contacto_proveedor": "+56 9 5158 6942",
    "correo_proveedor": "contacto@aislapanel.cl"
}



def process_pdfs_in_folder():
    pdf_folder = os.path.join(os.getcwd(), "pdfs")
    
    if not os.path.exists(pdf_folder):
        messagebox.showerror("Folder Not Found", f"The folder 'pdfs' does not exist in the current directory: {os.getcwd()}")
        return

    pdf_files = [file for file in os.listdir(pdf_folder) if file.lower().endswith('.pdf')]
    
    if not pdf_files:
        messagebox.showinfo("No PDFs Found", f"No PDF files found in the folder: {pdf_folder}")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        try:
            extracted_info = extract_quotation_info(pdf_path)
            update_cvs(extracted_info)
            print(f"Processed and updated CSV for: {pdf_file}")
        except Exception as e:
            print(f"Failed to process {pdf_file}: {e}")
            continue  # Proceed to the next file

    messagebox.showinfo("Process Complete", "All PDFs have been processed and the CSV has been updated.")

def load_products_by_provider(provider):
    products = []
    csv_file_path = "registry.csv"  # Ensure this path is correct
    print(f"Loading products for provider: {provider}")  # Debug print

    if not provider:
        return products
    
    # Read the CSV and filter products by provider
    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print(f"Row in CSV: {row}")  # Debug print to see each row
                if row['provider'] == provider:
                    print(f"Adding product: {row['description']}")  # Debug print for matching products
                    products.append(row['description'])  # Assuming the product description is in the 'description' field
    except FileNotFoundError:
        print("CSV file not found.")
    except KeyError:
        print("Check if 'provider' and 'description' columns exist in the CSV.")  # Handle missing columns
    
    print(f"Products found: {products}")  # Debug print to check products loaded
    return products

def update_product_list(product_listbox, provider):
    product_listbox.delete(0, tk.END)  # Clear current list
    products = load_products_by_provider(provider)  # Load products for the selected provider
    for product in products:
        product_listbox.insert(tk.END, product)  # Add each product to the listbox

async def main(extracted_info):

    
    if 'MAHUIDA' in extracted_info.get('addressee', '').upper():
        html_content = render_html('index.html', extracted_info)
    elif 'CAPITAL' in extracted_info.get('addressee', '').upper():
        html_content = render_html('index_copy.html', extracted_info)
    else:
        html_content = render_html('default_template.html', extracted_info)

    # Specify the directory where your CSS file is located
    css_directory = r''

    # Create the temporary HTML file in the same directory as your CSS file
    with tempfile.NamedTemporaryFile(suffix=".html", dir=css_directory, delete=False) as temp_html_file:
        temp_html_file.write(html_content.encode('utf-8'))
        temp_html_path = temp_html_file.name
    output_pdf = r"ORDEN DE COMPRA.pdf"
    
    await html_to_pdf(temp_html_path, output_pdf)

    # Optionally, delete the temporary HTML file after PDF generation
    os.remove(temp_html_path)

async def html_to_pdf(html_file, output_pdf):
    browser = await launch(headless=True, executablePath=r'chrome portable\GoogleChromePortable\GoogleChromePortable.exe')
    page = await browser.newPage()
    await page.goto(f'file:///{html_file}')
    await page.pdf({'path': output_pdf, 'format': 'A4'})
    await browser.close()

def render_html(template_path, context):
    env = Environment(loader=FileSystemLoader('.'))  # Load templates from the current directory
    template = env.get_template(template_path)  # Load the specific template
    return template.render(context)  # Render the template with the provided context

def extract_quotation_info(pdf_path):


    number = 0
    with open(r'nro_oc.txt', 'r') as file:
        number = int(file.read().strip())

    # Load the PDF document
    doc = fitz.open(pdf_path)
    
    # Extract text from the PDF
    text = ""
    for page in doc:
        text += page.get_text()

    # Convert text to uppercase to make searching case-insensitive
    text = text.upper()

    # Dictionary to store extracted information
    extracted_info = {}

    # Search for "MAHUIDA" or "CAPITAL" in the text and assign the corresponding addressee
    if re.search(r"MAHUIDA", text):
        extracted_info['addressee'] = "CONSTRUCTORA MAHUIDA"
    elif re.search(r"CAPITAL", text):
        extracted_info['addressee'] = "CONSTRUCTORA CAPITAL"
    else:
        extracted_info['addressee'] = "Unknown"


    if "MCT" in text:
            extracted_info.update(info_mct)
            fecha_oc = datetime.today().strftime('%d-%m-%Y')
            extracted_info['fecha_oc'] = fecha_oc
            extracted_info['forma_pago'] = "cheque 45 días"

            extracted_info['nro_oc'] = number
            number += 1
            with open('nro_oc.txt', 'w') as file:
                file.write(str(number))

            extracted_info['provider'] = "MCT"

            # Regex pattern to find the product code and ensure there is a newline after it
            code_pattern = r"(\n\d{4,5}-\d)([^\n])"
            text = re.sub(code_pattern, r"\1\n\2", text)

            date_issue_pattern = r"FECHA DE EMISIÓN\s*:\s*(\d{2}-\d{2}-\d{4})"
            quotation_number_pattern = r"COTIZACIÓN\s*N°\s*:\s*(\d+)"

            date_issue_match = re.search(date_issue_pattern, text)
            quotation_number_match = re.search(quotation_number_pattern, text)

            extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
            extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"

            # Process products
            start_index = text.find("SUB-TOTAL") + len("SUB-TOTAL")
            end_index = text.find("LA COLUMNA")
            
            if start_index != -1 and end_index != -1:
                product_text = text[start_index:end_index].strip()
                product_lines = product_text.splitlines()

                total_sum = 0

                for i in range(0, len(product_lines), 8):
                    if i + 7 < len(product_lines):
                        product_number = (i // 8) + 1
                        
                        # Parse quantity
                        quantity = float(product_lines[i + 3].strip().replace('.', '').replace(',', '.')) / 100
                        
                        # Parse unit price
                        raw_unit_price = product_lines[i + 6].strip()
                        cleaned_unit_price = raw_unit_price.replace(',', '').replace('.', '')

                        if len(cleaned_unit_price) > 2:
                            formatted_unit_price = cleaned_unit_price[:-2] + '.' + cleaned_unit_price[-2:]
                        else:
                            formatted_unit_price = '0.' + cleaned_unit_price.zfill(2)

                        unit_price = float(formatted_unit_price)
                        
                        # Calculate exact subtotal and apply rounding rule
                        exact_subtotal = quantity * unit_price
                        decimal_part = exact_subtotal - math.floor(exact_subtotal)
                        subtotal = math.ceil(exact_subtotal) if decimal_part >= 0.5 else math.floor(exact_subtotal)
                        
                        total_sum += subtotal

                        # Format for display
                        display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False)
                        display_subtotal = "$" + locale.currency(subtotal, grouping=True, symbol=False).split('.')[0]

                        # Store product information
                        extracted_info[f"item_number{product_number}"] = product_lines[i].strip()
                        extracted_info[f"code{product_number}"] = product_lines[i + 1].strip()
                        extracted_info[f"quantity{product_number}"] = str(quantity)
                        extracted_info[f"unit{product_number}"] = product_lines[i + 4].strip()
                        extracted_info[f"description{product_number}"] = product_lines[i + 5].strip()
                        extracted_info[f"unit_price{product_number}"] = display_unit_price
                        extracted_info[f"sub_total{product_number}"] = display_subtotal

                # Calculate totals using the same rounding logic
                total = total_sum  # total_sum is already properly rounded per item
                exact_tax = total * 0.19
                decimal_part_tax = exact_tax - math.floor(exact_tax)
                total_tax = math.ceil(exact_tax) if decimal_part_tax >= 0.5 else math.floor(exact_tax)
                
                exact_grand_total = total + total_tax
                decimal_part_grand = exact_grand_total - math.floor(exact_grand_total)
                grand_total = math.ceil(exact_grand_total) if decimal_part_grand >= 0.5 else math.floor(exact_grand_total)

                # Format totals for display
                extracted_info['total'] = "$" + locale.currency(total, grouping=True, symbol=False).split('.')[0]
                extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
                extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    elif "EBEMA" in text:
        extracted_info.update(info_ebema)
        fecha_oc = datetime.today().strftime('%d-%m-%Y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['provider'] = "EBEMA S.A."
        extracted_info['forma_pago'] = "cheque 45 días"
        extracted_info['nro_oc'] = number
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))


        date_issue_pattern = r"(\d{2}-\d{2}-\d{4})\s*FECHA"
        quotation_number_pattern = r"N°\s*(\d+)"

        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)

        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"

        # Add a newline before and after "PLANCHA"
        plancha_pattern = r"([^\n])?(PLANCHA)([^\n])"
        text = re.sub(plancha_pattern, r"\1\n\2\n\3", text, flags=re.IGNORECASE)

        # Add a newline before and after "METRO CUA"
        metro_cua_pattern = r"([^\n])?(METRO CUA)([^\n])"
        text = re.sub(metro_cua_pattern, r"\1\n\2\n\3", text, flags=re.IGNORECASE)

        # Add a newline before and after "KILOGRAMO"
        metro_cua_pattern = r"([^\n])?(KILOGRAMO)([^\n])"
        text = re.sub(metro_cua_pattern, r"\1\n\2\n\3", text, flags=re.IGNORECASE)

        # Clean up and process products
        start_index = text.find("TOTAL") + len("TOTAL")
        end_index = text.find("VIGENCIA HASTA:")
        print(start_index,end_index)
        
        if start_index != -1 and end_index != -1:
            product_text = text[start_index:end_index].strip()
            product_lines = product_text.splitlines()

            # Remove empty lines and trailing spaces
            product_lines = [line.strip() for line in product_lines if line.strip()]

            total_sum = 0

            # Process each product line in chunks of 7
            for i in range(0, len(product_lines), 7):  
                if i + 6 < len(product_lines):
                    product_number = (i // 7) + 1
                    
                    # Extract information for each product
                    item_number = product_lines[i]
                    code = product_lines[i + 1]
                    unit = product_lines[i + 2]
                    description = product_lines[i + 3].strip()
                    quantity = float(product_lines[i + 4].replace('.', '').replace(',', '.'))
                    unit_price = float(product_lines[i + 5].replace('.', '').replace(',', '.'))
                    
                    subtotal = round(quantity * unit_price)
                    total_sum += subtotal

                    # Formatting for display
                    display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                    display_subtotal = "$" + locale.currency(subtotal, grouping=True, symbol=False).split('.')[0]

                    extracted_info[f"item_number{product_number}"] = item_number
                    extracted_info[f"code{product_number}"] = code
                    extracted_info[f"unit{product_number}"] = unit
                    extracted_info[f"description{product_number}"] = description
                    extracted_info[f"quantity{product_number}"] = str(quantity)
                    extracted_info[f"unit_price{product_number}"] = display_unit_price
                    extracted_info[f"sub_total{product_number}"] = display_subtotal

            # Calculate totals
            total = round(total_sum)
            total_tax = round(total * 0.19)
            grand_total = round(total + total_tax)

            extracted_info['total'] = "$" + locale.currency(total, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    elif "COMERCIAL ADCO LTDA." in text:
        extracted_info.update(info_adco)
        fecha_oc = datetime.today().strftime('%d-%m-%Y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
        extracted_info['forma_pago'] = "cheque 30 días"
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        extracted_info['provider'] = "COMERCIAL ADCO LTDA."

        # Extract date of issue
        date_issue_pattern = r"(\d{2}-\d{2}-\d{4})"
        date_issue_match = re.search(date_issue_pattern, text)
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        quotation_number_pattern = r"ART\. SEGURIDAD INDUSTRIAL Y FERRETERIA\s+(\d{5})"
        quotation_number_match = re.search(quotation_number_pattern, text)
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"


        # Locate starting and ending indices
        start_phrase = "FONO: 045-2318391"
        end_phrase = "MIGUEL BRAVO SEGURA"
        start_index = text.find(start_phrase) + len(start_phrase)
        end_index = text.find(end_phrase)

        if start_index != -1 and end_index != -1:
            product_text = text[start_index:end_index].strip()
            product_lines = product_text.splitlines()

            # Remove empty lines and whitespace
            product_lines = [line.strip() for line in product_lines if line.strip()]

            total_sum = 0
            idx = 0  # Start from the first line

            product_number = 1  # To keep track of product numbers

            # Process the product lines
            while idx < len(product_lines):
                try:
                    # Skip the subtotal line (Line 1)
                    idx += 1  # Move to quantity line

                    # Line 2: Quantity
                    quantity_line = product_lines[idx]
                    quantity = float(quantity_line.replace('.', '').replace(',', '.'))

                    idx += 1  # Move to description line

                    # Line 3: Description
                    description_line = product_lines[idx]

                    idx += 1  # Move to unit price line

                    # Line 4: Unit Price
                    unit_price_line = product_lines[idx]
                    unit_price = float(unit_price_line.replace('.', '').replace(',', '.'))

                    idx += 1  # Move to code line

                    # Line 5: Code
                    code_line = product_lines[idx]

                    # Calculate subtotal
                    sub_total = round(quantity * unit_price)
                    total_sum += sub_total

                    # Format values for display
                    display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                    display_subtotal = "$" + locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]

                    # Store extracted info
                    extracted_info[f"item_number{product_number}"] = str(product_number)
                    extracted_info[f"code{product_number}"] = code_line
                    extracted_info[f"description{product_number}"] = description_line
                    extracted_info[f"quantity{product_number}"] = str(quantity)
                    extracted_info[f"unit_price{product_number}"] = display_unit_price
                    extracted_info[f"sub_total{product_number}"] = display_subtotal
                    extracted_info[f"unit{product_number}"] = "UN"  # Set unit as "UN"

                    # Prepare for next product
                    idx += 1  # Move to the next product's subtotal line
                    product_number += 1

                except (ValueError, IndexError) as e:
                    # Handle parsing errors or incomplete data
                    print(f"Error parsing product at index {idx}: {e}")
                    idx += 1  # Move to the next line to continue processing

            # Calculate totals
            total_tax = round(total_sum * 0.19)
            grand_total = round(total_sum + total_tax)

            extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]
    
    elif "AISLACENTRO LTDA" in text:
        extracted_info.update(info_aislacentro)
        fecha_oc = datetime.today().strftime('%d-%m-%Y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
        extracted_info['forma_pago'] = "cheque 30 días"
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        extracted_info['provider'] = "AISLACENTRO LTDA"

        quotation_number_pattern = r'Nro:\s*0*(\d{4,})'
        quotation_number_match = re.search(quotation_number_pattern, text,re.IGNORECASE)
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"


        # Extract date of issue
        date_issue_pattern = r"(\d{1,2} de [A-Za-z]+ de \d{4})"
        date_issue_match = re.search(date_issue_pattern, text)
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else fecha_oc

        # Locate starting and ending indices
        start_phrase = "NOMBRE RESPONSABLE"
        end_phrase = "OBSERVACIONES:"
    

        start_index = text.find(start_phrase) + len(start_phrase)
        end_index = text.find(end_phrase)
        print(start_index,end_index)
        if start_index != -1 and end_index != -1:
            product_text = text[start_index:end_index].strip()
            product_lines = product_text.splitlines()

            # Remove empty lines and whitespace
            product_lines = [line.strip() for line in product_lines if line.strip()]

            total_sum = 0
            idx = 0  # Start from the first line

            product_number = 1  # To keep track of product numbers

            # Process the product lines
            while idx + 6 < len(product_lines):
                try:
                    # Line 1: Quantity
                    quantity_line = product_lines[idx]
                    quantity = float(quantity_line.replace('.', '').replace(',', '.'))

                    # Line 2: Unit
                    unit_line = product_lines[idx + 1]
                    unit = unit_line

                    # Line 3: Description
                    description_line = product_lines[idx + 2]

                    # Line 4: List Price (ignored)
                    # idx + 3

                    # Line 5: Discount (ignored)
                    # idx + 4

                    # Line 6: Price
                    unit_price_line = product_lines[idx + 5]
                    unit_price = float(unit_price_line.replace('.', '').replace(',', '.'))

                    # Calculate subtotal
                    sub_total = quantity * unit_price
                    total_sum += sub_total

                    # Round up the displayed subtotal
                    display_subtotal_value = math.ceil(sub_total)

                    # Format values for display
                    display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                    display_subtotal = "$" + locale.currency(display_subtotal_value, grouping=True, symbol=False).split('.')[0]

                    # Store extracted info
                    extracted_info[f"item_number{product_number}"] = str(product_number)
                    extracted_info[f"code{product_number}"] = ''  # No code provided
                    extracted_info[f"description{product_number}"] = description_line
                    extracted_info[f"quantity{product_number}"] = str(quantity)
                    extracted_info[f"unit_price{product_number}"] = display_unit_price
                    extracted_info[f"sub_total{product_number}"] = display_subtotal
                    extracted_info[f"unit{product_number}"] = unit

                    # Prepare for next product
                    idx += 7  # Move to the next product's quantity line
                    product_number += 1

                except (ValueError, IndexError) as e:
                    # Handle parsing errors or incomplete data
                    print(f"Error parsing product at index {idx}: {e}")
                    idx += 1  # Move to the next line to continue processing

            # Calculate totals using actual subtotals
            total_tax = total_sum * 0.19
            grand_total = total_sum + total_tax

            # Round up totals for display
            display_total_value = math.ceil(total_sum)
            display_total_tax_value = math.ceil(total_tax)
            display_grand_total_value = math.ceil(grand_total)

            # Format totals for display
            extracted_info['total'] = "$" + locale.currency(display_total_value, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(display_total_tax_value, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(display_grand_total_value, grouping=True, symbol=False).split('.')[0]

    elif "AISLAPANEL" in text and "NOTA DE VENTA" in text:
        extracted_info.update(info_aislapanel_nv)
        extracted_info['provider'] = "AISLAPANEL S.A NV"
        fecha_oc = datetime.today().strftime('%d-%m-%Y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
        extracted_info['forma_pago'] = "cheque 30 días"
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        # Extract date and other details
        date_issue_pattern = r"FECHA\s*:\s*(\d{2}-\d{2}-\d{4})"
        quotation_number_pattern = r"NOTA DE VENTA\s*:\s*(\d+)"

        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)

        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"

        # Extract product information (including product codes)
        product_pattern = r"(\d+)\s+(PB\d{2}[A-Z]+\d{5}A)\s+(\d+,\d+)\s+(.+?)\s+([\d\.]+)\s+([\d\.]+)"
        products = re.findall(product_pattern, text, re.IGNORECASE)

        total_sum = 0

        for idx, product in enumerate(products, start=1):
            code = product[1]  # Extract the product code
            quantity = float(product[2].replace(",", "."))
            description = product[3].strip()
            unit_price = float(product[4].replace(".", "").replace(",", "."))
            sub_total = round(quantity * unit_price)
            total_sum += sub_total

            display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
            display_subtotal = "$" + locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]

            extracted_info[f"item_number{idx}"] = str(idx)
            extracted_info[f"code{idx}"] = code
            extracted_info[f"description{idx}"] = description
            extracted_info[f"quantity{idx}"] = str(quantity)
            extracted_info[f"unit_price{idx}"] = display_unit_price
            extracted_info[f"sub_total{idx}"] = display_subtotal

        total_tax = round(total_sum * 0.19)
        grand_total = round(total_sum + total_tax)

        extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
        extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
        extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    elif "AISLAPANEL" in text and "COTIZACION DE VENTA" in text:
        extracted_info.update(info_aislapanel_cv)
        extracted_info['provider'] = "AISLAPANEL S.A CV"
        fecha_oc = datetime.today().strftime('%d-%m-%Y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
        extracted_info['forma_pago'] = "cheque 30 días"
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        # Extract date and other details
        date_issue_pattern = r"FECHA DE EMISIÓN\s*:\s*(\d{2}-\d{2}-\d{4})"
        quotation_number_pattern = r"COTIZACION DE VENTA\s*:\s*(\d+)"

        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)

        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"

        # Extract product information (including product codes)
        product_pattern = r"(PB\d{2}[A-Z]+\d{5}A)\s+M2\s+(\d+,\d+)\s+(.+?)\s+([\d\.]+)\s+([\d\.]+)"
        products = re.findall(product_pattern, text, re.IGNORECASE)

        total_sum = 0

        for idx, product in enumerate(products, start=1):
            code = product[0]  # Extract the product code
            quantity = float(product[1].replace(",", "."))
            description = product[2].strip()
            unit_price = float(product[3].replace(".", "").replace(",", "."))
            sub_total = round(quantity * unit_price)
            total_sum += sub_total

            display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
            display_subtotal = "$" + locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]

            extracted_info[f"item_number{idx}"] = str(idx)
            extracted_info[f"code{idx}"] = code
            extracted_info[f"description{idx}"] = description
            extracted_info[f"quantity{idx}"] = str(quantity)
            extracted_info[f"unit_price{idx}"] = display_unit_price
            extracted_info[f"sub_total{idx}"] = display_subtotal

        total_tax = round(total_sum * 0.19)
        grand_total = round(total_sum + total_tax)

        extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
        extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
        extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    print(extracted_info)
    return extracted_info

def update_cvs(extracted_info):
    # Define the CSV file path
    csv_file_path = os.path.join(os.getcwd(), "registry.csv")

    # Define the headers for the CSV
    headers = [
        "index", "quotation_number", "nro_oc", "provider", "date_of_quotation",
        "code", "description", "unit_price", "quantity",
        "addressee", "vendedor", "direccion_proveedor", "ubicacion_proveedor",
        "contacto_proveedor", "correo_proveedor", "fecha_oc", "forma_pago", "unidad"
    ]

    # Prepare the general info
    quotation_number = extracted_info.get('quotation_number', 'Unknown')
    nro_oc = extracted_info.get('nro_oc', 'Unknown')
    provider = extracted_info.get('provider', 'Unknown')
    date_of_quotation = extracted_info.get('date_of_issue', 'Unknown')
    addressee = extracted_info.get('addressee', 'Unknown')
    vendedor = extracted_info.get('vendedor', 'Unknown')
    direccion_proveedor = extracted_info.get('direccion_proveedor', 'Unknown')
    ubicacion_proveedor = extracted_info.get('ubicacion_proveedor', 'Unknown')
    contacto_proveedor = extracted_info.get('contacto_proveedor', 'Unknown')
    correo_proveedor = extracted_info.get('correo_proveedor', 'Unknown')
    fecha_oc = extracted_info.get('fecha_oc', 'Unknown')
    forma_pago = extracted_info.get('forma_pago', 'Unknown')

    # Read existing CSV data to check for duplicates
    existing_entries = []
    if os.path.isfile(csv_file_path):
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_quotation_number = row.get('quotation_number', 'Unknown')
                existing_nro_oc = row.get('nro_oc', 'Unknown')
                existing_entries.append((existing_quotation_number, existing_nro_oc))

    # Check if the quotation_number or nro_oc already exists
    is_duplicate = False
    for existing_quotation_number, existing_nro_oc in existing_entries:
        if (quotation_number != 'Unknown' and quotation_number == existing_quotation_number) or \
           (nro_oc != 'Unknown' and nro_oc == existing_nro_oc):
            is_duplicate = True
            break  # Duplicate found, no need to check further

    if is_duplicate:
        print(f"Entry with quotation_number '{quotation_number}' or nro_oc '{nro_oc}' already exists. Skipping update.")
        return  # Do not update the CSV

    # Determine the starting index
    index = 1  # Default starting index
    if os.path.isfile(csv_file_path):
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            indices = [int(row['index']) for row in reader if row.get('index', '').isdigit()]
            if indices:
                index = max(indices) + 1

    # Prepare rows for each product
    rows = []
    idx = 1
    while f"description{idx}" in extracted_info:
        code = extracted_info.get(f"code{idx}", 'Unknown')
        description = extracted_info.get(f"description{idx}", 'Unknown')
        unit_price = extracted_info.get(f"unit_price{idx}", 'Unknown')
        quantity = extracted_info.get(f"quantity{idx}", 'Unknown')
        unit = extracted_info.get(f"unit{idx}", 'Unknown')
        row = {
            "index": index,
            "quotation_number": quotation_number,
            "nro_oc": nro_oc,
            "provider": provider,
            "date_of_quotation": date_of_quotation,
            "code": code,
            "description": description,
            "unit_price": unit_price,
            "quantity": quantity,
            "addressee": addressee,
            "vendedor": vendedor,
            "direccion_proveedor": direccion_proveedor,
            "ubicacion_proveedor": ubicacion_proveedor,
            "contacto_proveedor": contacto_proveedor,
            "correo_proveedor": correo_proveedor,
            "fecha_oc": fecha_oc,
            "forma_pago": forma_pago,
            "unidad": unit
        }
        rows.append(row)
        index += 1
        idx += 1

    # Write to CSV
    file_exists = os.path.isfile(csv_file_path)

    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        # Write headers if file does not exist
        if not file_exists:
            writer.writeheader()
        # Write rows
        writer.writerows(rows)

    print(f"Data saved to {csv_file_path}")

def generate_purchase_order(nro_oc_input, provider_input, order_items):
    # Validate NRO OC input
    try:
        nro_oc = int(nro_oc_input)
    except ValueError:
        tk.messagebox.showerror("Invalid NRO OC", "Please enter a valid NRO OC number.")
        return

    # Build extracted_info dictionary
    extracted_info = {
        'addressee': 'CONSTRUCTORA CAPITAL',
        'fecha_oc': datetime.today().strftime('%d-%m-%y'),
        'date_of_issue': datetime.today().strftime('%d-%m-%y'),
        'nro_oc': nro_oc,
        'provider': provider_input,
        'forma_pago': "cheque 30 días"  # Assuming default payment method
    }

    # Update provider-specific fields
    if provider_input == 'EBEMA S.A.':
        extracted_info.update(info_ebema)
    elif provider_input == 'MCT':
        extracted_info.update(info_mct)
    elif provider_input == 'COMERCIAL ADCO LTDA.':
        extracted_info.update(info_adco)
    elif provider_input == 'AISLACENTRO LTDA':
        extracted_info.update(info_aislacentro)
    elif provider_input == 'AISLAPANEL S.A NV':
        extracted_info.update(info_aislapanel_nv)
    elif provider_input == 'AISLAPANEL S.A CV':
        extracted_info.update(info_aislapanel_cv)
    else:
        tk.messagebox.showerror("Unknown Provider", f"No information available for provider '{provider_input}'.")
        return

    # Add products to extracted_info
    for idx, item in enumerate(order_items, start=1):
        extracted_info[f"description{idx}"] = item['description']
        extracted_info[f"quantity{idx}"] = item['quantity_var'].get()
        extracted_info[f"unit_price{idx}"] = "$" + locale.currency(item['unit_price'], grouping=True, symbol=False).split('.')[0]
        # Calculate subtotal
        subtotal = calculate_subtotal(item['unit_price'], item['quantity_var'].get())
        extracted_info[f"sub_total{idx}"] = "$" + locale.currency(subtotal, grouping=True, symbol=False).split('.')[0]
        # Add code and unit
        extracted_info[f"code{idx}"] = item['product_code']
        extracted_info[f"unit{idx}"] = item.get('product_unit', 'Unknown')

    # Calculate total, tax, and grand total
    total = sum(calculate_subtotal(item['unit_price'], item['quantity_var'].get()) for item in order_items)
    total_tax = round(total * 0.19)
    grand_total = round(total + total_tax)

    extracted_info['total'] = "$" + locale.currency(total, grouping=True, symbol=False).split('.')[0]
    extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
    extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    # Generate the purchase order
    print(f"Generating purchase order with nro_oc: {extracted_info['nro_oc']}")
    asyncio.run(main(extracted_info))

    # Do not update the CSV when using this method
    # update_cvs(extracted_info)

def open_new_ui():
    new_window = tk.Toplevel()  # Create a new window
    new_window.title("OC desde datos")
    new_window.geometry("600x700")

    # Label for product list
    product_label = tk.Label(new_window, text="Products for Selected Provider:")
    product_label.pack(pady=5)

    # Frame to hold the products and a scrollbar
    product_frame = tk.Frame(new_window)
    product_frame.pack(pady=5, fill=tk.BOTH, expand=True)

    # Create a canvas inside the frame
    canvas = tk.Canvas(product_frame)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add a scrollbar to the canvas
    scrollbar = tk.Scrollbar(product_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas with the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Create a frame inside the canvas to hold the product widgets
    products_inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=products_inner_frame, anchor='nw')

    # Variable to store the selected provider
    provider_var = tk.StringVar(new_window)
    provider_var.set("EBEMA")  # Default value

    # Function to update the product list based on the selected provider
    def update_products(*args):
        # Clear the existing products
        for widget in products_inner_frame.winfo_children():
            widget.destroy()

        products = load_products_by_provider(provider_var.get())

        for idx, product in enumerate(products):
            product_label = tk.Label(products_inner_frame, text=product)
            product_label.grid(row=idx, column=0, sticky='w', padx=5, pady=2)

            add_button = tk.Button(products_inner_frame, text="Add", command=lambda p=product: add_product_to_order(p))
            add_button.grid(row=idx, column=1, padx=5)

    provider_var.trace('w', update_products)
    update_products()  # Initial call to populate the list

    # Dropdown for provider selection
    provider_label = tk.Label(new_window, text="Select Provider:")
    provider_label.pack(pady=5)

    provider_dropdown = tk.OptionMenu(new_window, provider_var, "EBEMA S.A.", "MCT", "COMERCIAL ADCO LTDA.", "AISLACENTRO LTDA", "AISLAPANEL S.A NV", "AISLAPANEL S.A CV")
    provider_dropdown.pack(pady=5)

    # Area to display selected products
    order_label = tk.Label(new_window, text="Products in Order:")
    order_label.pack(pady=5)

    order_frame = tk.Frame(new_window)
    order_frame.pack(pady=5, fill=tk.BOTH, expand=True)

    # List to hold order items
    order_items = []

    # Function to add product to the order
    def add_product_to_order(product_description):
        # Check if the product is already added
        for item in order_items:
            if item['description'] == product_description:
                tk.messagebox.showinfo("Product already added", f"The product '{product_description}' is already added.")
                return

        # Fetch latest price, code, and unit from CSV
        unit_price, product_code, product_unit = get_latest_product_info(provider_var.get(), product_description)

        # Create a frame for the product entry
        product_row = tk.Frame(order_frame)
        product_row.pack(fill='x', pady=2)

        # Product description label
        product_label = tk.Label(product_row, text=product_description)
        product_label.pack(side='left', padx=5)

        # Quantity entry
        quantity_var = tk.StringVar(value="1")
        quantity_entry = tk.Entry(product_row, textvariable=quantity_var, width=5)
        quantity_entry.pack(side='left', padx=5)

        # Unit label
        unit_label = tk.Label(product_row, text=f"Unit: {product_unit}")
        unit_label.pack(side='left', padx=5)

        # Unit price label
        unit_price_label = tk.Label(product_row, text=f"Unit Price: ${unit_price:,.2f}")
        unit_price_label.pack(side='left', padx=5)

        # Subtotal label
        subtotal_var = tk.StringVar()
        subtotal = calculate_subtotal(unit_price, quantity_var.get())
        subtotal_var.set(f"Subtotal: ${subtotal:,.2f}")
        subtotal_label = tk.Label(product_row, textvariable=subtotal_var)
        subtotal_label.pack(side='left', padx=5)

        # Update subtotal when quantity changes
        def on_quantity_change(*args):
            qty = quantity_var.get()
            new_subtotal = calculate_subtotal(unit_price, qty)
            subtotal_var.set(f"Subtotal: ${new_subtotal:,.2f}")

        quantity_var.trace_add('write', on_quantity_change)

        # Add product details to order_items
        order_items.append({
            'description': product_description,
            'quantity_var': quantity_var,
            'unit_price': unit_price,
            'subtotal_var': subtotal_var,
            'product_code': product_code,
            'product_unit': product_unit  # Include unit
        })


    # Label and Entry for nro_oc input5555555555555555555555555555555555555555
    nro_oc_label = tk.Label(new_window, text="Enter NRO OC:")
    nro_oc_label.pack(pady=5)

    nro_oc_entry = tk.Entry(new_window)
    nro_oc_entry.pack(pady=5)

    # Button to generate the purchase order
    generar_button = tk.Button(new_window, text="Generar", command=lambda: generate_purchase_order(nro_oc_entry.get(), provider_var.get(), order_items))
    generar_button.pack(pady=10)

def get_latest_product_info(provider, product_description):
    csv_file_path = "registry.csv"
    latest_price = None
    latest_code = None
    latest_unit = None
    latest_date = None  # To keep track of the latest quotation date

    date_format = '%d-%m-%Y'  # Adjust this format to match your CSV date format

    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['provider'] == provider and row['description'] == product_description:
                    # Parse the date_of_quotation
                    date_str = row.get('date_of_quotation', '').strip()
                    if not date_str:
                        continue  # Skip if date_of_quotation is missing

                    try:
                        row_date = datetime.strptime(date_str, date_format)
                    except ValueError:
                        print(f"Invalid date format in row: {date_str}")
                        continue  # Skip rows with invalid date formats

                    # Compare dates to find the most recent one
                    if latest_date is None or row_date > latest_date:
                        latest_date = row_date

                        # Clean and parse unit_price
                        price_str = row['unit_price'].replace("$", "").replace(",", "").strip()
                        try:
                            latest_price = float(price_str)
                        except ValueError:
                            latest_price = 0.0  # Default to 0.0 if parsing fails

                        latest_code = row.get('code', 'Unknown')
                        latest_unit = row.get('unidad', 'Unknown')

        if latest_price is not None and latest_code is not None and latest_unit is not None:
            return latest_price, latest_code, latest_unit
        else:
            # Return defaults if not found
            return 0.0, 'Unknown', 'Unknown'

    except Exception as e:
        print(f"Error fetching product info: {e}")
        return 0.0, 'Unknown', 'Unknown'

def calculate_subtotal(unit_price, quantity):
    try:
        quantity = float(quantity)
        subtotal = unit_price * quantity
        return subtotal
    except ValueError:
        return 0.0

def on_drop(event):
    file_path = event.data.strip("{}")  # Get the dropped file path
    if os.path.isfile(file_path):  # Ensure it's a valid file
        # Step 1: Extract information from the PDF
        extracted_info = extract_quotation_info(file_path)
        
        # Step 2: Update the CSV file with the extracted information
        update_cvs(extracted_info)
        
        # Step 3: Generate the PDF file asynchronously
        asyncio.run(main(extracted_info))  # Call the async function 'main'

    else:
        print("No valid file was dropped")

def setup_gui():
    root = TkinterDnD.Tk()  # Using TkinterDnD for drag-and-drop functionality
    root.title("Drag and Drop PDF files")
    root.geometry("400x300")

    # Label for drag-and-drop functionality
    label = tk.Label(root, text="Drag and drop your PDF file here", width=40, height=4)
    label.pack(pady=10)

    # Bind the drop event to the window
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', on_drop)

    # Button to open the new UI for "OC desde datos"
    oc_datos_button = tk.Button(root, text="OC desde datos", command=open_new_ui)
    oc_datos_button.pack(pady=20)

    # New button to process PDFs in the 'pdfs' folder
    actualizar_base_button = tk.Button(root, text="Actualizar Base", command=process_pdfs_in_folder)
    actualizar_base_button.pack(pady=10)

    root.mainloop()

setup_gui()