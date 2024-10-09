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

# Set locale for currency formatting
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Dictionaries containing provider-specific information
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

# (Other provider dictionaries go here...)

# Function to extract information from a PDF
def extract_quotation_info(pdf_path):
    number = 0
    with open(r'C:\Users\jfrit\Desktop\PROYECTOS\vscode\ordencomprahtml\nro_oc.txt', 'r') as file:
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
        fecha_oc = datetime.today().strftime('%d-%m-%y')
        extracted_info['fecha_oc'] = fecha_oc

        extracted_info['nro_oc'] = number
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        extracted_info['provider'] = "Electrocom S.A."

        # Removed the pattern for 'addressee', now handled with the plain text search above

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
                    quantity = float(product_lines[i + 3].strip().replace('.', '').replace(',', '.')) / 100
                    
                    raw_unit_price = product_lines[i + 6].strip().replace('.', '').replace(',', '')
                    formatted_unit_price = raw_unit_price[:-2] + '.' + raw_unit_price[-2:]
                    unit_price = float(formatted_unit_price)
                    
                    subtotal = round(quantity * unit_price)
                    total_sum += subtotal

                    display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                    display_subtotal = "$" + locale.currency(subtotal, grouping=True, symbol=False).split('.')[0]

                    extracted_info[f"item_number{product_number}"] = product_lines[i].strip()
                    extracted_info[f"code{product_number}"] = product_lines[i + 1].strip()
                    extracted_info[f"quantity{product_number}"] = str(quantity)
                    extracted_info[f"unit{product_number}"] = product_lines[i + 4].strip()
                    extracted_info[f"description{product_number}"] = product_lines[i + 5].strip()
                    extracted_info[f"unit_price{product_number}"] = display_unit_price
                    extracted_info[f"sub_total{product_number}"] = display_subtotal

        total = round(total_sum)
        total_tax = round(total * 0.19)
        grand_total = round(total + total_tax)

        extracted_info['total'] = "$" + locale.currency(total, grouping=True, symbol=False).split('.')[0]
        extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
        extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    elif "EBEMA" in text:
        extracted_info.update(info_ebema)
        fecha_oc = datetime.today().strftime('%d-%m-%y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        extracted_info['provider'] = "EBEMA S.A."

        date_issue_pattern = r"(\d{2}-\d{2}-\d{4})\s*FECHA"
        quotation_number_pattern = r"N°\s*(\d+)"

        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)

        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"

        # Preprocess text to add space after unit measures
        unit_correction_pattern = r"(\d+)\s+(PLANCHA)([A-Z])"
        text = re.sub(unit_correction_pattern, r"\1 \2 \3", text, flags=re.IGNORECASE)

        product_pattern = r"(\d+)\s+(\d+)\s+(UNIDAD|ROLLO|PLANCHA|UN|CAJA|MTS|SACO|UN|CS|METRO CUA)\s+(.+?)\s+([\d\.]+)\s+([\d\.]+)"
        products = re.findall(product_pattern, text, re.IGNORECASE)

        total_sum = 0

        for idx, product in enumerate(products, start=1):
            quantity = float(product[4].replace('.', '').replace(',', '.'))
            unit_price = float(product[5].replace('.', '').replace(',', '.'))
            subtotal = round(quantity * unit_price)
            total_sum += subtotal
            
            display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
            display_subtotal = "$" + locale.currency(subtotal, grouping=True, symbol=False).split('.')[0]

            extracted_info[f"item_number{idx}"] = product[0]
            extracted_info[f"code{idx}"] = product[1]
            extracted_info[f"unit{idx}"] = product[2]
            extracted_info[f"description{idx}"] = product[3].strip()
            extracted_info[f"quantity{idx}"] = str(quantity)
            extracted_info[f"unit_price{idx}"] = display_unit_price
            extracted_info[f"sub_total{idx}"] = display_subtotal

        total = round(total_sum)
        total_tax = round(total * 0.19)
        grand_total = round(total + total_tax)

        extracted_info['total'] = "$" + locale.currency(total, grouping=True, symbol=False).split('.')[0]
        extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
        extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    elif "COMERCIAL ADCO LTDA." in text:
        extracted_info.update(info_adco)
        fecha_oc = datetime.today().strftime('%d-%m-%y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        extracted_info['provider'] = "COMERCIAL ADCO LTDA."

        date_issue_pattern = r"FECHA\s*:\s*(\d{2}-\d{2}-\d{4})"
        date_issue_match = re.search(date_issue_pattern, text)
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"

        product_pattern = r"(\d+)\s+(\d+,\d{2})\s+(.+?)\s+(\d{1,3}(?:\.\d{3})*)\s+(\d{1,3}(?:\.\d{3})*)"
        products = re.findall(product_pattern, text, re.IGNORECASE)

        total_sum = 0
        for idx, product in enumerate(products, start=1):
            item_number = str(idx)
            code = product[0]
            quantity = float(product[1].replace(",", "."))
            description = product[2].strip()
            unit_price = float(product[3].replace(".", "").replace(",", "."))
            sub_total = round(quantity * unit_price, 2)
            total_sum += sub_total

            display_unit_price = locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
            display_subtotal = locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]

            extracted_info[f"item_number{idx}"] = item_number
            extracted_info[f"code{idx}"] = code
            extracted_info[f"description{idx}"] = description
            extracted_info[f"quantity{idx}"] = str(quantity)
            extracted_info[f"unit_price{idx}"] = display_unit_price
            extracted_info[f"sub_total{idx}"] = display_subtotal

        total_tax = round(total_sum * 0.19, 2)
        grand_total = round(total_sum + total_tax, 2)

        extracted_info['total'] = locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
        extracted_info['total_tax'] = locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
        extracted_info['grand_total'] = locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    elif "AISLACENTRO LTDA" in text:
        extracted_info.update(info_aislacentro)
        fecha_oc = datetime.today().strftime('%d-%m-%y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
        number += 1
        with open('nro_oc.txt', 'w') as file:
            file.write(str(number))

        extracted_info['provider'] = "AISLACENTRO LTDA"

        date_issue_pattern = r"(\d{2}\s*DE\s*AGOSTO\s*DE\s*\d{4})"
        quotation_number_pattern = r"NRO:\s*(\d+)"

        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)

        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"

        product_pattern = r"(\d+,\d+)\s+UD\s+(.+?)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)"
        products = re.findall(product_pattern, text, re.IGNORECASE)

        total_sum = 0

        for idx, product in enumerate(products, start=1):
            quantity = float(product[0].replace(",", "."))
            description = product[1].strip()
            unit_price = float(product[2].replace(".", "").replace(",", "."))
            sub_total = round(quantity * unit_price)
            total_sum += sub_total

            display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
            display_subtotal = "$" + locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]

            extracted_info[f"item_number{idx}"] = str(idx)
            extracted_info[f"description{idx}"] = description
            extracted_info[f"quantity{idx}"] = str(quantity)
            extracted_info[f"unit_price{idx}"] = display_unit_price
            extracted_info[f"sub_total{idx}"] = display_subtotal

        total_tax = round(total_sum * 0.19)
        grand_total = round(total_sum + total_tax)

        extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
        extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
        extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]


        extracted_info.update(info_aislapanel_cv)
        fecha_oc = datetime.today().strftime('%d-%m-%y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
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

        # Extract product information
        product_pattern = r"(\w+)\s+(\w+)\s+(\d+,\d+)\s+(.+?)\s+([\d\.]+)\s+([\d\.]+)"
        products = re.findall(product_pattern, text, re.IGNORECASE)

        total_sum = 0

        for idx, product in enumerate(products, start=1):
            quantity = float(product[2].replace(",", "."))
            description = product[3].strip()
            unit_price = float(product[4].replace(".", "").replace(",", "."))
            sub_total = round(quantity * unit_price)
            total_sum += sub_total

            display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
            display_subtotal = "$" + locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]

            extracted_info[f"item_number{idx}"] = str(idx)
            extracted_info[f"description{idx}"] = description
            extracted_info[f"quantity{idx}"] = str(quantity)
            extracted_info[f"unit_price{idx}"] = display_unit_price
            extracted_info[f"sub_total{idx}"] = display_subtotal

        total_tax = round(total_sum * 0.19)
        grand_total = round(total_sum + total_tax)

        extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
        extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
        extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]

    elif "AISLAPANEL" in text and "NOTA DE VENTA" in text:
        extracted_info.update(info_aislapanel_nv)
        fecha_oc = datetime.today().strftime('%d-%m-%y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
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
        fecha_oc = datetime.today().strftime('%d-%m-%y')
        extracted_info['fecha_oc'] = fecha_oc
        extracted_info['nro_oc'] = number
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

# Function to render HTML using extracted info
def render_html(template_path, context):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_path)
    return template.render(context)

# Asynchronous function to convert HTML to PDF
async def html_to_pdf(html_file, output_pdf):
    browser = await launch(headless=True, executablePath=r'C:\Users\jfrit\Desktop\PROYECTOS\chrome portable\GoogleChromePortable\GoogleChromePortable.exe')
    page = await browser.newPage()
    await page.goto(f'file:///{html_file}')
    await page.pdf({'path': output_pdf, 'format': 'A4'})
    await browser.close()

# Main function that processes a single file
async def process_pdf(pdf_path):
    extracted_info = extract_quotation_info(pdf_path)
    context = extracted_info

    if 'MAHUIDA' in extracted_info.get('addressee', '').upper():
        html_content = render_html('index.html', context)
    elif 'CAPITAL' in extracted_info.get('addressee', '').upper():
        html_content = render_html('index_copy.html', context)
    else:
        html_content = render_html('default_template.html', context)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html_file:
        temp_html_file.write(html_content.encode('utf-8'))
        temp_html_path = temp_html_file.name

    output_pdf = f'O.C.N°{extracted_info["nro_oc"]} {extracted_info["provider"]}.pdf'
    await html_to_pdf(temp_html_path, output_pdf)
    os.remove(temp_html_path)

# Drag and drop window function
def drag_and_drop():
    def on_drop(event):
        files = root.tk.splitlist(event.data)  # Extract the dropped file paths
        for file_path in files:
            if file_path.endswith(".pdf"):
                asyncio.run(process_pdf(file_path))  # Process the PDF
            else:
                print("Please drop a PDF file.")

    root = TkinterDnD.Tk()
    root.title("Drag and Drop PDF files")
    root.geometry("400x200")

    label = tk.Label(root, text="Drag and drop your PDF file here", width=40, height=4)
    label.pack(pady=40)

    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', on_drop)

    root.mainloop()

if __name__ == '__main__':
    drag_and_drop()
