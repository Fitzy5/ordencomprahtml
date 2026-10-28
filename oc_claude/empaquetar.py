#!/usr/bin/env python3
"""
Empaqueta la carpeta oc_claude/ en un zip para que el usuario la reemplace en
su PC y haga commit + push manualmente.

Uso:
    python empaquetar.py "<motivo>" [--salida ARCHIVO.zip]

El zip contiene una carpeta raíz "oc_claude/" con todo menos output/,
archivos temporales y __pycache__. Incluye CAMBIOS.txt con el motivo, la fecha
y el correlativo, que sirve de mensaje de commit.
"""

import argparse
import os
import zipfile
from datetime import datetime

EXCLUIR_DIRS = {"output", "__pycache__", ".git"}
EXCLUIR_ARCH = {"_oc_tmp.html", "CAMBIOS.txt"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("motivo", help="Qué cambió, p.ej. 'OC N°1033 EBEMA S.A. (cotización 1059456)'")
    ap.add_argument("--salida")
    ap.add_argument("--base", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()

    base = args.base
    ahora = datetime.now()
    with open(os.path.join(base, "nro_oc.txt")) as f:
        nro = f.read().strip()

    salida = args.salida or os.path.join(
        base, "output", f"oc_claude_{ahora:%Y-%m-%d_%H%M}.zip")
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)

    cambios = (f"{args.motivo}\n\n"
               f"Generado: {ahora:%d-%m-%Y %H:%M}\n"
               f"Próxima OC (nro_oc.txt): {nro}\n\n"
               "Instrucciones:\n"
               "1. Abre el zip y copia la carpeta oc_claude encima de la del repo\n"
               "   (reemplazar archivos).\n"
               "2. En GitHub Desktop revisa los cambios, usa la primera línea de\n"
               "   este archivo como mensaje de commit y haz Push origin.\n"
               "3. Haz el push ANTES de pedir la siguiente OC, o el correlativo\n"
               "   se repetirá.\n")

    n = 0
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for raiz, dirs, archivos in os.walk(base):
            dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRS]
            for a in archivos:
                if a in EXCLUIR_ARCH or a.endswith(".zip"):
                    continue
                ruta = os.path.join(raiz, a)
                z.write(ruta, os.path.join("oc_claude", os.path.relpath(ruta, base)))
                n += 1
        z.writestr("oc_claude/CAMBIOS.txt", cambios)

    print(f"Zip generado: {salida}")
    print(f"  {n} archivos | próxima OC: {nro} | motivo: {args.motivo}")


if __name__ == "__main__":
    main()
