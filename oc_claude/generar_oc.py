#!/usr/bin/env python3
"""
Genera una orden de compra en PDF a partir de un JSON con los datos de la cotización.

Uso:
    python generar_oc.py datos.json [--salida ARCHIVO.pdf] [--numero N]
                                    [--sin-registro] [--forzar] [--base DIR]

Flujo:
  1. Valida el JSON y calcula subtotales, neto, IVA (19%) y total.
  2. Si el JSON trae "verificacion" (los totales que dice el PDF de la
     cotización), los compara: si no cuadran, aborta (salvo --forzar).
  3. Revisa duplicados en registry.csv (misma cotización + proveedor).
  4. Recién entonces consume el correlativo de nro_oc.txt.
  5. Renderiza plantilla_oc.html y lo imprime a PDF con Playwright.
  6. Si todo salió bien: incrementa nro_oc.txt y agrega filas a registry.csv.

Formato del JSON de entrada (lo produce Claude al leer la cotización):
{
  "empresa": "MAHUIDA",                  // o "CAPITAL"
  "proveedor": "AISLACENTRO LTDA",       // debe existir en providers.csv
  "nro_cotizacion": "22155",
  "fecha_cotizacion": "13-10-2026",
  "forma_pago": "cheque 30 días",        // opcional (default por proveedor abajo)
  "condicion_entrega": "retiro bodega",  // opcional
  "items": [
    {"codigo": "", "descripcion": "BASE PRO EIFS SACO 22,7KG ETCO",
     "cantidad": 41, "unidad": "UD", "precio_unitario": 8720}
  ],
  "verificacion": {"neto": 695520, "iva": 132149, "total": 827669}  // opcional
}
"""

import argparse
import csv
import json
import os
import sys
import unicodedata
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

IVA = Decimal("0.19")

# Formas de pago por defecto por proveedor (se puede sobreescribir en el JSON)
FORMA_PAGO_DEFAULT = {
    "MCT": "cheque 45 días",
    "EBEMA S.A.": "cheque 45 días",
}
FORMA_PAGO_GENERICA = "cheque 30 días"
CONDICION_ENTREGA_DEFAULT = "retiro bodega"
# Texto fijo del recuadro "Comentarios o instrucciones especiales" (no se toma del JSON)
COMENTARIOS_FIJOS = "STOCK BODEGA LABRANZA"


# ---------------------------------------------------------------- utilidades
def normalizar(s):
    """minúsculas y sin tildes, para comparar nombres de proveedor."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


def d(x):
    return Decimal(str(x))


def redondear(x):
    """Redondeo comercial a peso entero (mitad hacia arriba)."""
    return int(d(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def fmt_clp(n, decimales=False):
    """$1.234.567 con puntos de miles; decimales con coma solo si existen."""
    n = d(n)
    entero = int(n)
    resto = (n - entero).quantize(Decimal("0.01"))
    s = f"{entero:,}".replace(",", ".")
    if decimales and resto != 0:
        s += "," + f"{resto:.2f}".split(".")[1]
    return "$" + s


def fmt_cantidad(c):
    c = d(c)
    if c == c.to_integral_value():
        return str(int(c))
    return f"{c.normalize()}".replace(".", ",")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---------------------------------------------------------------- datos base
def cargar_proveedor(base, nombre):
    ruta = os.path.join(base, "providers.csv")
    with open(ruta, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if normalizar(row["provider"]) == normalizar(nombre):
                return row
    disponibles = []
    with open(ruta, newline="", encoding="utf-8") as f:
        disponibles = [r["provider"] for r in csv.DictReader(f)]
    sys.exit(
        f"ERROR: proveedor '{nombre}' no está en providers.csv.\n"
        f"Proveedores conocidos: {', '.join(disponibles)}\n"
        f"Agrega la fila a providers.csv y vuelve a intentar."
    )


def existe_duplicado(base, nro_cotizacion, proveedor):
    ruta = os.path.join(base, "registry.csv")
    if not os.path.isfile(ruta):
        return None
    with open(ruta, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (str(row.get("quotation_number", "")).strip() == str(nro_cotizacion).strip()
                    and normalizar(row.get("provider", "")) == normalizar(proveedor)):
                return row.get("nro_oc", "?")
    return None


# ---------------------------------------------------------------- cálculo
def calcular(datos):
    filas = []
    neto = 0
    for it in datos["items"]:
        cant = d(it["cantidad"])
        precio = d(it["precio_unitario"])
        sub = redondear(cant * precio)
        neto += sub
        filas.append({**it, "_sub": sub, "_cant": cant, "_precio": precio})
    iva = redondear(d(neto) * IVA)
    total = neto + iva
    return filas, neto, iva, total


def verificar(datos, neto, iva, total, forzar):
    v = datos.get("verificacion")
    if not v:
        print("AVISO: el JSON no trae 'verificacion'; no se cruzaron totales con la cotización.")
        return
    problemas = []
    for campo, calculado in (("neto", neto), ("iva", iva), ("total", total)):
        if campo in v and v[campo] is not None:
            declarado = redondear(v[campo])
            if abs(declarado - calculado) > 2:  # tolerancia $2 por redondeos del emisor
                problemas.append(f"  {campo}: cotización dice {declarado:,}, calculado {calculado:,}")
    if problemas:
        msg = "LOS TOTALES NO CUADRAN con la cotización:\n" + "\n".join(problemas)
        if forzar:
            print("AVISO (--forzar): " + msg)
        else:
            sys.exit("ERROR: " + msg + "\nRevisa los ítems extraídos. Usa --forzar para generar igual.")
    else:
        print("Verificación OK: neto/IVA/total cuadran con la cotización.")


# ---------------------------------------------------------------- render
def render(base, datos, prov, filas, neto, iva, total, nro_oc, fecha_oc):
    with open(os.path.join(base, "empresas.json"), encoding="utf-8") as f:
        empresas = json.load(f)
    emp = empresas.get(datos.get("empresa", "MAHUIDA").upper())
    if not emp:
        sys.exit(f"ERROR: empresa '{datos.get('empresa')}' no está en empresas.json (usa MAHUIDA o CAPITAL).")

    with open(os.path.join(base, "plantilla_oc.html"), encoding="utf-8") as f:
        html = f.read()

    filas_html = []
    for it in filas:
        filas_html.append(
            "      <tr>"
            f"<td class=\"ctr\">{esc(it.get('codigo') or '')}</td>"
            f"<td>{esc(it['descripcion'])}</td>"
            f"<td class=\"ctr\">{fmt_cantidad(it['_cant'])}</td>"
            f"<td class=\"ctr\">{esc(it.get('unidad') or 'UN')}</td>"
            f"<td class=\"num\">{fmt_clp(it['_precio'], decimales=True)}</td>"
            f"<td class=\"num total-col\">{fmt_clp(it['_sub'])}</td>"
            "</tr>"
        )
    # Relleno visual: mínimo 14 filas para que la tabla se parezca al formato clásico
    for _ in range(max(0, 14 - len(filas))):
        filas_html.append(
            "      <tr><td>&nbsp;</td><td></td><td></td><td></td><td></td>"
            "<td class=\"total-col\"></td></tr>"
        )

    forma_pago = datos.get("forma_pago") or FORMA_PAGO_DEFAULT.get(
        prov["provider"], FORMA_PAGO_GENERICA)

    valores = {
        "razon_social_l1": esc(emp["razon_social_l1"]),
        "razon_social_l2": esc(emp["razon_social_l2"]),
        "direccion": esc(emp["direccion"]),
        "ciudad": esc(emp["ciudad"]),
        "telefono": esc(emp["telefono"]),
        "sitio_web": esc(emp["sitio_web"]),
        "logo": emp["logo"],
        "contacto": esc(emp["contacto"]),
        "fecha_oc": esc(fecha_oc),
        "nro_oc": str(nro_oc),
        "vendedor": esc(prov.get("vendedor", "")),
        "proveedor": esc(prov["provider"]),
        "direccion_proveedor": esc(prov.get("direccion_proveedor", "")),
        "ubicacion_proveedor": esc(prov.get("ubicacion_proveedor", "")),
        "contacto_proveedor": esc(prov.get("contacto_proveedor", "")),
        "correo_proveedor": esc(prov.get("correo_proveedor", "")),
        "forma_pago": esc(forma_pago),
        "condicion_entrega": esc(datos.get("condicion_entrega") or CONDICION_ENTREGA_DEFAULT),
        "nro_cotizacion": esc(datos["nro_cotizacion"]),
        "comentarios": esc(COMENTARIOS_FIJOS),
        "total": fmt_clp(neto),
        "total_iva": fmt_clp(iva),
        "envio": "0",
        "otro": "0",
        "gran_total": fmt_clp(total),
        "FILAS": "\n".join(filas_html),
    }
    for k, v in valores.items():
        html = html.replace("{{" + k + "}}", v)
    return html, forma_pago


def html_a_pdf(base, html, salida):
    from playwright.sync_api import sync_playwright
    tmp = os.path.join(base, "_oc_tmp.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("file://" + os.path.abspath(tmp))
            page.pdf(path=salida, format="A4", print_background=True,
                     margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            browser.close()
    finally:
        os.remove(tmp)


# ---------------------------------------------------------------- registro
def actualizar_registro(base, datos, prov, filas, nro_oc, fecha_oc, forma_pago):
    ruta = os.path.join(base, "registry.csv")
    headers = ["index", "quotation_number", "nro_oc", "provider", "date_of_quotation",
               "code", "description", "unit_price", "quantity", "addressee", "vendedor",
               "direccion_proveedor", "ubicacion_proveedor", "contacto_proveedor",
               "correo_proveedor", "fecha_oc", "forma_pago", "unidad"]
    indice = 1
    existe = os.path.isfile(ruta)
    if existe:
        with open(ruta, newline="", encoding="utf-8") as f:
            nums = [int(r["index"]) for r in csv.DictReader(f)
                    if str(r.get("index", "")).isdigit()]
            if nums:
                indice = max(nums) + 1
    addressee = "CONSTRUCTORA MAHUIDA" if datos.get("empresa", "MAHUIDA").upper() == "MAHUIDA" \
        else "CONSTRUCTORA CAPITAL"
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        if not existe:
            w.writeheader()
        for it in filas:
            w.writerow({
                "index": indice,
                "quotation_number": datos["nro_cotizacion"],
                "nro_oc": nro_oc,
                "provider": prov["provider"],
                "date_of_quotation": datos.get("fecha_cotizacion", ""),
                "code": it.get("codigo") or "",
                "description": it["descripcion"],
                "unit_price": fmt_clp(it["_precio"], decimales=True),
                "quantity": str(it["_cant"]),
                "addressee": addressee,
                "vendedor": prov.get("vendedor", ""),
                "direccion_proveedor": prov.get("direccion_proveedor", ""),
                "ubicacion_proveedor": prov.get("ubicacion_proveedor", ""),
                "contacto_proveedor": prov.get("contacto_proveedor", ""),
                "correo_proveedor": prov.get("correo_proveedor", ""),
                "fecha_oc": fecha_oc,
                "forma_pago": forma_pago,
                "unidad": it.get("unidad") or "UN",
            })
            indice += 1
    print(f"registry.csv actualizado ({len(filas)} filas, desde índice {indice - len(filas)}).")


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="Genera una orden de compra en PDF.")
    ap.add_argument("json_entrada", help="Archivo JSON con los datos de la cotización")
    ap.add_argument("--salida", help="Ruta del PDF de salida")
    ap.add_argument("--numero", type=int, help="Forzar un número de OC específico (no toca nro_oc.txt)")
    ap.add_argument("--sin-registro", action="store_true", help="No escribir en registry.csv ni nro_oc.txt")
    ap.add_argument("--forzar", action="store_true", help="Generar aunque haya duplicado o los totales no cuadren")
    ap.add_argument("--base", default=os.path.dirname(os.path.abspath(__file__)),
                    help="Directorio con plantilla, providers.csv, registry.csv y nro_oc.txt")
    args = ap.parse_args()
    base = args.base

    with open(args.json_entrada, encoding="utf-8") as f:
        datos = json.load(f)

    for campo in ("proveedor", "nro_cotizacion", "items"):
        if not datos.get(campo):
            sys.exit(f"ERROR: falta el campo '{campo}' en el JSON.")

    prov = cargar_proveedor(base, datos["proveedor"])
    filas, neto, iva, total = calcular(datos)
    verificar(datos, neto, iva, total, args.forzar)

    dup = existe_duplicado(base, datos["nro_cotizacion"], prov["provider"])
    if dup and not args.forzar and not args.numero:
        sys.exit(f"ERROR: la cotización {datos['nro_cotizacion']} de {prov['provider']} "
                 f"ya tiene la OC N°{dup} en registry.csv. Usa --forzar para repetirla.")

    # correlativo: solo ahora se consume
    ruta_nro = os.path.join(base, "nro_oc.txt")
    if args.numero:
        nro_oc = args.numero
    else:
        with open(ruta_nro) as f:
            nro_oc = int(f.read().strip())

    fecha_oc = datetime.today().strftime("%d-%m-%Y")
    html, forma_pago = render(base, datos, prov, filas, neto, iva, total, nro_oc, fecha_oc)

    salida = args.salida or os.path.join(base, "output", f"O.C.N°{nro_oc} {prov['provider']}.pdf")
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    html_a_pdf(base, html, salida)
    print(f"PDF generado: {salida}")
    print(f"  OC N°{nro_oc} | {prov['provider']} | cotización {datos['nro_cotizacion']}")
    print(f"  Neto {fmt_clp(neto)} | IVA {fmt_clp(iva)} | Total {fmt_clp(total)}")

    if not args.sin_registro:
        if not args.numero:
            with open(ruta_nro, "w") as f:
                f.write(str(nro_oc + 1))
            print(f"nro_oc.txt -> {nro_oc + 1}")
        actualizar_registro(base, datos, prov, filas, nro_oc, fecha_oc, forma_pago)


if __name__ == "__main__":
    main()
