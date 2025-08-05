import os
import fitz  # PyMuPDF
import re
from jinja2 import Environment, FileSystemLoader
import asyncio
from pyppeteer import launch
import tempfile
import locale
import tkinter as tk
from tkinter import messagebox, Toplevel
from tkinterdnd2 import TkinterDnD, DND_FILES
import csv
import math
import pyperclip  # For clipboard access
import logging  # For logging actions
from datetime import datetime

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set locale for currency formatting
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Set working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print("Current working directory set to:", os.getcwd())
print("Files in CWD:", os.listdir(os.getcwd()))

# Provider information
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

def review_and_correct_text(initial_text, provider):
    """Open a modal window to display and edit text, retrieve corrected text from clipboard."""
    pyperclip.copy(initial_text)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f"extracted_text_{provider}_{timestamp}.txt", "w", encoding='utf-8') as f:
        f.write(initial_text)
    logging.info(f"Saved extracted text for {provider} to extracted_text_{provider}_{timestamp}.txt")
    top = Toplevel()
    top.title(f"Review Parsed Text for {provider}")
    top.grab_set()
    message = tk.Label(top, text="The extracted text has been copied to the clipboard.\nPlease review it, make corrections if necessary, and copy the corrected text back to the clipboard.")
    message.pack(pady=10)
    text_area = tk.Text(top, height=20, width=80)
    text_area.insert(tk.END, initial_text)
    text_area.pack(pady=10)
    result = [None]
    
    def on_submit():
        if messagebox.askyesno("Confirm", "Have you copied the corrected text to the clipboard?"):
            result[0] = pyperclip.paste()
            top.destroy()
        else:
            messagebox.showinfo("Retry", "Please copy the corrected text to the clipboard and try again.")
    
    def on_cancel():
        result[0] = None
        top.destroy()
    
    submit_button = tk.Button(top, text="Submit", command=on_submit)
    submit_button.pack(side=tk.LEFT, padx=10, pady=10)
    cancel_button = tk.Button(top, text="Cancel", command=on_cancel)
    cancel_button.pack(side=tk.RIGHT, padx=10, pady=10)
    
    top.wait_window()
    if result[0] is None:
        logging.warning(f"User cancelled text correction for {provider}")
        return None
    with open(f"corrected_text_{provider}_{timestamp}.txt", "w", encoding='utf-8') as f:
        f.write(result[0])
    logging.info(f"Saved corrected text for {provider} to corrected_text_{provider}_{timestamp}.txt")
    return result[0]

def extract_quotation_info(pdf_path):
    """Extract information from a quotation PDF."""
    number = 0
    try:
        with open('nro_oc.txt', 'r') as file:
            number = int(file.read().strip())
    except FileNotFoundError:
        logging.warning("nro_oc.txt not found, starting with number 0")
    
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    text = text.upper()
    extracted_info = {}
    
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
        
        code_pattern = r"(\n\d{4,5}-\d)([^\n])"
        text = re.sub(code_pattern, r"\1\n\2", text)
        date_issue_pattern = r"FECHA DE EMISIÓN\s*:\s*(\d{2}-\d{2}-\d{4})"
        quotation_number_pattern = r"COTIZACIÓN\s*N°\s*:\s*(\d+)"
        
        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)
        
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"
        
        start_index = text.find("SUB-TOTAL") + len("SUB-TOTAL")
        end_index = text.find("LA COLUMNA")
        if start_index == -1 or end_index == -1:
            logging.error("Could not find product boundaries for MCT")
            messagebox.showerror("Error", "Could not find product boundaries for MCT")
            return None
        product_text = text[start_index:end_index].strip()
        corrected_text = review_and_correct_text(product_text, "MCT")
        if corrected_text is None:
            return None
        try:
            product_lines = corrected_text.splitlines()
            total_sum = 0
            for i in range(0, len(product_lines), 8):
                if i + 7 < len(product_lines):
                    product_number = (i // 8) + 1
                    quantity = float(product_lines[i + 3].strip().replace('.', '').replace(',', '.')) / 100
                    raw_unit_price = product_lines[i + 6].strip()
                    cleaned_unit_price = raw_unit_price.replace(',', '').replace('.', '')
                    if len(cleaned_unit_price) > 2:
                        formatted_unit_price = cleaned_unit_price[:-2] + '.' + cleaned_unit_price[-2:]
                    else:
                        formatted_unit_price = '0.' + cleaned_unit_price.zfill(2)
                    unit_price = float(formatted_unit_price)
                    exact_subtotal = quantity * unit_price
                    decimal_part = exact_subtotal - math.floor(exact_subtotal)
                    subtotal = math.ceil(exact_subtotal) if decimal_part >= 0.5 else math.floor(exact_subtotal)
                    total_sum += subtotal
                    display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False)
                    display_subtotal = "$" + locale.currency(subtotal, grouping=True, symbol=False).split('.')[0]
                    extracted_info[f"item_number{product_number}"] = product_lines[i].strip()
                    extracted_info[f"code{product_number}"] = product_lines[i + 1].strip()
                    extracted_info[f"quantity{product_number}"] = str(quantity)
                    extracted_info[f"unit{product_number}"] = product_lines[i + 4].strip()
                    extracted_info[f"description{product_number}"] = product_lines[i + 5].strip()
                    extracted_info[f"unit_price{product_number}"] = display_unit_price
                    extracted_info[f"sub_total{product_number}"] = display_subtotal
            total = total_sum
            exact_tax = total * 0.19
            decimal_part_tax = exact_tax - math.floor(exact_tax)
            total_tax = math.ceil(exact_tax) if decimal_part_tax >= 0.5 else math.floor(exact_tax)
            exact_grand_total = total + total_tax
            decimal_part_grand = exact_grand_total - math.floor(exact_grand_total)
            grand_total = math.ceil(exact_grand_total) if decimal_part_grand >= 0.5 else math.floor(exact_grand_total)
            extracted_info['total'] = "$" + locale.currency(total, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]
        except Exception as e:
            logging.error(f"Error parsing MCT products: {e}")
            messagebox.showerror("Parsing Error", f"Failed to parse products for MCT: {e}")
            return None
    
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
        
        plancha_pattern = r"([^\n])?(PLANCHA)([^\n])"
        text = re.sub(plancha_pattern, r"\1\n\2\n\3", text, flags=re.IGNORECASE)
        metro_cua_pattern = r"([^\n])?(METRO CUA|KILOGRAMO)([^\n])"
        text = re.sub(metro_cua_pattern, r"\1\n\2\n\3", text, flags=re.IGNORECASE)
        
        start_index = text.find("TOTAL") + len("TOTAL")
        end_index = text.find("VIGENCIA HASTA:")
        if start_index == -1 or end_index == -1:
            logging.error("Could not find product boundaries for EBEMA")
            messagebox.showerror("Error", "Could not find product boundaries for EBEMA")
            return None
        product_text = text[start_index:end_index].strip()
        corrected_text = review_and_correct_text(product_text, "EBEMA")
        if corrected_text is None:
            return None
        try:
            product_lines = [line.strip() for line in corrected_text.splitlines() if line.strip()]
            total_sum = 0
            for i in range(0, len(product_lines), 7):
                if i + 6 < len(product_lines):
                    product_number = (i // 7) + 1
                    item_number = product_lines[i]
                    code = product_lines[i + 1]
                    unit = product_lines[i + 2]
                    description = product_lines[i + 3].strip()
                    quantity = float(product_lines[i + 4].replace('.', '').replace(',', '.'))
                    unit_price = float(product_lines[i + 5].replace('.', '').replace(',', '.'))
                    subtotal = round(quantity * unit_price)
                    total_sum += subtotal
                    display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                    display_subtotal = "$" + locale.currency(subtotal, grouping=True, symbol=False).split('.')[0]
                    extracted_info[f"item_number{product_number}"] = item_number
                    extracted_info[f"code{product_number}"] = code
                    extracted_info[f"unit{product_number}"] = unit
                    extracted_info[f"description{product_number}"] = description
                    extracted_info[f"quantity{product_number}"] = str(quantity)
                    extracted_info[f"unit_price{product_number}"] = display_unit_price
                    extracted_info[f"sub_total{product_number}"] = display_subtotal
            total = round(total_sum)
            total_tax = round(total * 0.19)
            grand_total = round(total + total_tax)
            extracted_info['total'] = "$" + locale.currency(total, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]
        except Exception as e:
            logging.error(f"Error parsing EBEMA products: {e}")
            messagebox.showerror("Parsing Error", f"Failed to parse products for EBEMA: {e}")
            return None
    
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
        
        date_issue_pattern = r"(\d{2}-\d{2}-\d{4})"
        
        date_issue_match = re.search(date_issue_pattern, text)
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        
        # Differentiate between COTIZACIÓN and NOTA DE VENTA
        if "COTIZACION" in text:
            quotation_number_pattern = r"ART\. SEGURIDAD INDUSTRIAL Y FERRETERIA\s+(\d{5})"
            quotation_number_match = re.search(quotation_number_pattern, text)
            extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"
            
            start_phrase = "FONO: 045-2318391"
            end_phrase = "MIGUEL BRAVO SEGURA"
            start_index = text.find(start_phrase) + len(start_phrase)
            end_index = text.find(end_phrase)
            if start_index == -1 or end_index == -1:
                logging.error("Could not find product boundaries for ADCO COTIZACIÓN")
                messagebox.showerror("Error", "Could not find product boundaries for ADCO COTIZACIÓN")
                return None
            product_text = text[start_index:end_index].strip()
            corrected_text = review_and_correct_text(product_text, "ADCO_COTIZACION")
            if corrected_text is None:
                return None
            try:
                product_lines = [line.strip() for line in corrected_text.splitlines() if line.strip()]
                total_sum = 0
                idx = 0
                product_number = 1
                while idx < len(product_lines):
                    try:
                        idx += 1  # Skip the subtotal line
                        quantity_line = product_lines[idx]
                        quantity = float(quantity_line.replace('.', '').replace(',', '.'))
                        idx += 1
                        description_line = product_lines[idx]
                        idx += 1
                        unit_price_line = product_lines[idx]
                        unit_price = float(unit_price_line.replace('.', '').replace(',', '.'))
                        idx += 1
                        code_line = product_lines[idx]
                        sub_total = round(quantity * unit_price)
                        total_sum += sub_total
                        display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                        display_subtotal = "$" + locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]
                        extracted_info[f"item_number{product_number}"] = str(product_number)
                        extracted_info[f"code{product_number}"] = code_line
                        extracted_info[f"description{product_number}"] = description_line
                        extracted_info[f"quantity{product_number}"] = str(quantity)
                        extracted_info[f"unit_price{product_number}"] = display_unit_price
                        extracted_info[f"sub_total{product_number}"] = display_subtotal
                        extracted_info[f"unit{product_number}"] = "UN"
                        idx += 1
                        product_number += 1
                    except (ValueError, IndexError) as e:
                        logging.error(f"Error parsing ADCO COTIZACIÓN product at index {idx}: {e}")
                        idx += 1
                total_tax = round(total_sum * 0.19)
                grand_total = round(total_sum + total_tax)
                extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
                extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
                extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]
            except Exception as e:
                logging.error(f"Error parsing ADCO COTIZACIÓN products: {e}")
                messagebox.showerror("Parsing Error", f"Failed to parse products for ADCO COTIZACIÓN: {e}")
                return None
        
        elif "NOTA DE VENTA" in text:
            quotation_number_pattern = r"NOTA DE VENTA\s+(\d+)"
            quotation_number_match = re.search(quotation_number_pattern, text)
            extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"
            
            start_phrase = "045-2318391"
            end_phrase = "MIGUEL BRAVO SEGURA"
            start_index = text.find(start_phrase) + len(start_phrase)
            end_index = text.find(end_phrase)
            if start_index == -1 or end_index == -1:
                logging.error("Could not find product boundaries for ADCO NOTA DE VENTA")
                messagebox.showerror("Error", "Could not find product boundaries for ADCO NOTA DE VENTA")
                return None
            product_text = text[start_index:end_index].strip()
            corrected_text = review_and_correct_text(product_text, "ADCO_NOTA_DE_VENTA")
            if corrected_text is None:
                return None
            try:
                product_lines = [line.strip() for line in corrected_text.splitlines() if line.strip()]
                total_sum = 0
                idx = 0
                product_number = 1
                while idx < len(product_lines):
                    try:
                        idx += 1  # Skip the subtotal line
                        quantity_line = product_lines[idx]
                        quantity = float(quantity_line.replace('.', '').replace(',', '.'))
                        idx += 1
                        code_line = product_lines[idx]
                        idx += 1
                        description_line = product_lines[idx]
                        idx += 1
                        unit_price_line = product_lines[idx]
                        unit_price = float(unit_price_line.replace('.', '').replace(',', '.'))
                        sub_total = round(quantity * unit_price)
                        total_sum += sub_total
                        display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                        display_subtotal = "$" + locale.currency(sub_total, grouping=True, symbol=False).split('.')[0]
                        extracted_info[f"item_number{product_number}"] = str(product_number)
                        extracted_info[f"code{product_number}"] = code_line
                        extracted_info[f"description{product_number}"] = description_line
                        extracted_info[f"quantity{product_number}"] = str(quantity)
                        extracted_info[f"unit_price{product_number}"] = display_unit_price
                        extracted_info[f"sub_total{product_number}"] = display_subtotal
                        extracted_info[f"unit{product_number}"] = "UN"
                        idx += 1
                        product_number += 1
                    except (ValueError, IndexError) as e:
                        logging.error(f"Error parsing ADCO NOTA DE VENTA product at index {idx}: {e}")
                        idx += 1
                total_tax = round(total_sum * 0.19)
                grand_total = round(total_sum + total_tax)
                extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
                extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
                extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]
            except Exception as e:
                logging.error(f"Error parsing ADCO NOTA DE VENTA products: {e}")
                messagebox.showerror("Parsing Error", f"Failed to parse products for ADCO NOTA DE VENTA: {e}")
                return None
    
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
        quotation_number_match = re.search(quotation_number_pattern, text, re.IGNORECASE)
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"
        
        date_issue_pattern = r"(\d{1,2} de [A-Za-z]+ de \d{4})"
        date_issue_match = re.search(date_issue_pattern, text)
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else fecha_oc
        
        start_phrase = "NOMBRE RESPONSABLE"
        end_phrase = "OBSERVACIONES:"
        start_index = text.find(start_phrase) + len(start_phrase)
        end_index = text.find(end_phrase)
        if start_index == -1 or end_index == -1:
            logging.error("Could not find product boundaries for AISLACENTRO")
            messagebox.showerror("Error", "Could not find product boundaries for AISLACENTRO")
            return None
        product_text = text[start_index:end_index].strip()
        corrected_text = review_and_correct_text(product_text, "AISLACENTRO")
        if corrected_text is None:
            return None
        try:
            product_lines = [line.strip() for line in corrected_text.splitlines() if line.strip()]
            total_sum = 0
            idx = 0
            product_number = 1
            while idx + 6 < len(product_lines):
                try:
                    quantity_line = product_lines[idx]
                    quantity = float(quantity_line.replace('.', '').replace(',', '.'))
                    unit_line = product_lines[idx + 1]
                    unit = unit_line
                    description_line = product_lines[idx + 2]
                    unit_price_line = product_lines[idx + 5]
                    unit_price = float(unit_price_line.replace('.', '').replace(',', '.'))
                    sub_total = quantity * unit_price
                    total_sum += sub_total
                    display_subtotal_value = math.ceil(sub_total)
                    display_unit_price = "$" + locale.currency(unit_price, grouping=True, symbol=False).split('.')[0]
                    display_subtotal = "$" + locale.currency(display_subtotal_value, grouping=True, symbol=False).split('.')[0]
                    extracted_info[f"item_number{product_number}"] = str(product_number)
                    extracted_info[f"code{product_number}"] = ''
                    extracted_info[f"description{product_number}"] = description_line
                    extracted_info[f"quantity{product_number}"] = str(quantity)
                    extracted_info[f"unit_price{product_number}"] = display_unit_price
                    extracted_info[f"sub_total{product_number}"] = display_subtotal
                    extracted_info[f"unit{product_number}"] = unit
                    idx += 7
                    product_number += 1
                except (ValueError, IndexError) as e:
                    logging.error(f"Error parsing AISLACENTRO product at index {idx}: {e}")
                    idx += 1
            total_tax = total_sum * 0.19
            grand_total = total_sum + total_tax
            display_total_value = math.ceil(total_sum)
            display_total_tax_value = math.ceil(total_tax)
            display_grand_total_value = math.ceil(grand_total)
            extracted_info['total'] = "$" + locale.currency(display_total_value, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(display_total_tax_value, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(display_grand_total_value, grouping=True, symbol=False).split('.')[0]
        except Exception as e:
            logging.error(f"Error parsing AISLACENTRO products: {e}")
            messagebox.showerror("Parsing Error", f"Failed to parse products for AISLACENTRO: {e}")
            return None
    
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
        
        date_issue_pattern = r"FECHA\s*:\s*(\d{2}-\d{2}-\d{4})"
        quotation_number_pattern = r"NOTA DE VENTA\s*:\s*(\d+)"
        
        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)
        
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"
        
        product_text = text
        corrected_text = review_and_correct_text(product_text, "AISLAPANEL_NV")
        if corrected_text is None:
            return None
        try:
            product_pattern = r"(\d+)\s+(PB\d{2}[A-Z]+\d{5}A)\s+(\d+,\d+)\s+(.+?)\s+([\d\.]+)\s+([\d\.]+)"
            products = re.findall(product_pattern, corrected_text, re.IGNORECASE)
            total_sum = 0
            for idx, product in enumerate(products, start=1):
                code = product[1]
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
                extracted_info[f"unit{idx}"] = "Unknown"
            total_tax = round(total_sum * 0.19)
            grand_total = round(total_sum + total_tax)
            extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]
        except Exception as e:
            logging.error(f"Error parsing AISLAPANEL NV products: {e}")
            messagebox.showerror("Parsing Error", f"Failed to parse products for AISLAPANEL NV: {e}")
            return None
    
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
        
        date_issue_pattern = r"FECHA DE EMISIÓN\s*:\s*(\d{2}-\d{2}-\d{4})"
        quotation_number_pattern = r"COTIZACION DE VENTA\s*:\s*(\d+)"
        
        date_issue_match = re.search(date_issue_pattern, text)
        quotation_number_match = re.search(quotation_number_pattern, text)
        
        extracted_info['date_of_issue'] = date_issue_match.group(1) if date_issue_match else "Unknown"
        extracted_info['quotation_number'] = quotation_number_match.group(1) if quotation_number_match else "Unknown"
        
        product_text = text
        corrected_text = review_and_correct_text(product_text, "AISLAPANEL_CV")
        if corrected_text is None:
            return None
        try:
            product_pattern = r"(PB\d{2}[A-Z]+\d{5}A)\s+M2\s+(\d+,\d+)\s+(.+?)\s+([\d\.]+)\s+([\d\.]+)"
            products = re.findall(product_pattern, corrected_text, re.IGNORECASE)
            total_sum = 0
            for idx, product in enumerate(products, start=1):
                code = product[0]
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
                extracted_info[f"unit{idx}"] = "Unknown"
            total_tax = round(total_sum * 0.19)
            grand_total = round(total_sum + total_tax)
            extracted_info['total'] = "$" + locale.currency(total_sum, grouping=True, symbol=False).split('.')[0]
            extracted_info['total_tax'] = "$" + locale.currency(total_tax, grouping=True, symbol=False).split('.')[0]
            extracted_info['grand_total'] = "$" + locale.currency(grand_total, grouping=True, symbol=False).split('.')[0]
        except Exception as e:
            logging.error(f"Error parsing AISLAPANEL CV products: {e}")
            messagebox.showerror("Parsing Error", f"Failed to parse products for AISLAPANEL CV: {e}")
            return None
    
    print(extracted_info)
    return extracted_info

async def html_to_pdf(html_path, pdf_path):
    """Convert HTML to PDF using local Chromium."""
    executable_path = r'C:\GoogleChromePortable64\GoogleChromePortable.exe'
    if not os.path.isfile(executable_path):
        logging.error(f"Chromium executable not found at {executable_path}")
        messagebox.showerror("Error", f"Chromium executable not found at {executable_path}. Please check the path.")
        return False
    os.environ['PYPPETEER_NO_CHROMIUM_DOWNLOAD'] = '1'
    try:
        browser = await launch(
            headless=True,
            executablePath=executable_path,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await browser.newPage()
        await page.goto(f'file:///{html_path}')
        await page.pdf({'path': pdf_path, 'format': 'A4'})
        await browser.close()
        logging.info(f"Successfully generated PDF: {pdf_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to generate PDF: {e}")
        messagebox.showerror("PDF Generation Error", f"Failed to generate PDF: {e}")
        return False

async def main(extracted_info):
    """Generate purchase order PDF."""
    if 'MAHUIDA' in extracted_info.get('addressee', '').upper():
        html_content = render_html('index.html', extracted_info)
    elif 'CAPITAL' in extracted_info.get('addressee', '').upper():
        html_content = render_html('index_copy.html', extracted_info)
    else:
        html_content = render_html('default_template.html', extracted_info)
    
    css_directory = ''
    with tempfile.NamedTemporaryFile(suffix=".html", dir=css_directory, delete=False) as temp_html_file:
        temp_html_file.write(html_content.encode('utf-8'))
        temp_html_path = temp_html_file.name
    
    output_pdf = "ORDEN DE COMPRA.pdf"
    success = await html_to_pdf(temp_html_path, output_pdf)
    
    try:
        os.remove(temp_html_path)
    except Exception as e:
        logging.warning(f"Failed to remove temporary HTML file {temp_html_path}: {e}")
    
    if success:
        messagebox.showinfo("Success", f"Purchase order PDF generated: {output_pdf}")
    else:
        messagebox.showerror("Error", "Failed to generate purchase order PDF. Check app.log for details.")

def on_drop(event):
    """Handle dropped PDF files."""
    file_path = event.data.strip("{}")
    if os.path.isfile(file_path) and file_path.lower().endswith('.pdf'):
        extracted_info = extract_quotation_info(file_path)
        if extracted_info is not None:
            update_cvs(extracted_info)
            asyncio.run(main(extracted_info))
            messagebox.showinfo("Success", f"Processed {file_path} and generated purchase order.")
        else:
            logging.warning(f"Skipped {file_path} due to parsing issues or cancellation")
            messagebox.showinfo("Cancelled", "Operation cancelled due to parsing issues or user cancellation.")
    else:
        logging.error(f"Invalid file dropped: {file_path}")
        messagebox.showerror("Error", "No valid PDF file was dropped.")

def process_pdfs_in_folder():
    """Process all PDFs in the 'pdfs' folder."""
    pdf_folder = os.path.join(os.getcwd(), "pdfs")
    if not os.path.exists(pdf_folder):
        messagebox.showerror("Folder Not Found", f"The folder 'pdfs' does not exist in {os.getcwd()}")
        return
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        messagebox.showinfo("No PDFs Found", f"No PDF files found in {pdf_folder}")
        return
    for pdf_file in pdf_files:
        file_path = os.path.join(pdf_folder, pdf_file)
        extracted_info = extract_quotation_info(file_path)
        if extracted_info is not None:
            update_cvs(extracted_info)
            asyncio.run(main(extracted_info))
            print(f"Processed and updated CSV for: {pdf_file}")
        else:
            logging.warning(f"Skipped {pdf_file} due to parsing issues or cancellation")
            print(f"Skipped {pdf_file} due to parsing issues or cancellation.")
    messagebox.showinfo("Process Complete", "All PDFs have been processed and the CSV has been updated.")

def update_cvs(extracted_info):
    """Update registry.csv with extracted information."""
    csv_file_path = os.path.join(os.getcwd(), "registry.csv")
    headers = [
        "index", "quotation_number", "nro_oc", "provider", "date_of_quotation",
        "code", "description", "unit_price", "quantity",
        "addressee", "vendedor", "direccion_proveedor", "ubicacion_proveedor",
        "contacto_proveedor", "correo_proveedor", "fecha_oc", "forma_pago", "unidad"
    ]
    
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
    
    existing_entries = []
    if os.path.isfile(csv_file_path):
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_quotation_number = row.get('quotation_number', 'Unknown')
                existing_nro_oc = row.get('nro_oc', 'Unknown')
                existing_entries.append((existing_quotation_number, existing_nro_oc))
    
    is_duplicate = False
    for existing_quotation_number, existing_nro_oc in existing_entries:
        if (quotation_number != 'Unknown' and quotation_number == existing_quotation_number) or \
           (nro_oc != 'Unknown' and nro_oc == existing_nro_oc):
            is_duplicate = True
            break
    if is_duplicate:
        logging.warning(f"Duplicate entry for quotation {quotation_number} or nro_oc {nro_oc}")
        return
    
    index = 1
    if os.path.isfile(csv_file_path):
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            indices = [int(row['index']) for row in reader if row.get('index', '').isdigit()]
            if indices:
                index = max(indices) + 1
    
    rows = []
    idx = 1
    while f"description{idx}" in extracted_info:
        row = {
            "index": index,
            "quotation_number": quotation_number,
            "nro_oc": nro_oc,
            "provider": provider,
            "date_of_quotation": date_of_quotation,
            "code": extracted_info.get(f"code{idx}", 'Unknown'),
            "description": extracted_info.get(f"description{idx}", 'Unknown'),
            "unit_price": extracted_info.get(f"unit_price{idx}", 'Unknown'),
            "quantity": extracted_info.get(f"quantity{idx}", 'Unknown'),
            "addressee": addressee,
            "vendedor": vendedor,
            "direccion_proveedor": direccion_proveedor,
            "ubicacion_proveedor": ubicacion_proveedor,
            "contacto_proveedor": contacto_proveedor,
            "correo_proveedor": correo_proveedor,
            "fecha_oc": fecha_oc,
            "forma_pago": forma_pago,
            "unidad": extracted_info.get(f"unit{idx}", 'Unknown')
        }
        rows.append(row)
        index += 1
        idx += 1
    
    file_exists = os.path.isfile(csv_file_path)
    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    logging.info(f"Updated CSV with {len(rows)} rows for nro_oc {nro_oc}")

def render_html(template_path, context):
    """Render HTML template with context."""
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_path)
    return template.render(context)

def setup_gui():
    """Set up the Tkinter GUI for drag-and-drop."""
    root = TkinterDnD.Tk()
    root.title("Drag and Drop PDF files")
    root.geometry("400x300")
    label = tk.Label(root, text="Drag and drop your PDF file here", width=40, height=4)
    label.pack(pady=10)
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', on_drop)
    actualizar_base_button = tk.Button(root, text="Actualizar Base", command=process_pdfs_in_folder)
    actualizar_base_button.pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    setup_gui()