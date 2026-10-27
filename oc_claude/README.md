# Órdenes de compra con Claude (oc_claude)

Reemplaza el parsing por regex de `final.py`: **Claude lee la cotización** (cualquier
proveedor, incluso escaneada) y produce un JSON estándar; este módulo hace el resto
de forma determinista.

## Archivos

| Archivo | Rol |
|---|---|
| `generar_oc.py` | JSON → validación → correlativo → PDF → registro |
| `plantilla_oc.html` | Plantilla única (Mahuida y Capital), sin límite de ítems |
| `empresas.json` | Datos de encabezado de cada constructora |
| `logos/` | Logos recortados de los formatos originales |
| `providers.csv` | **Única fuente** de datos de proveedores (antes duplicados en el script) |
| `registry.csv` | Historial de precios/órdenes (mismo formato que antes) |
| `nro_oc.txt` | Correlativo de OC |

## Uso

```bash
python generar_oc.py datos.json                 # flujo completo
python generar_oc.py datos.json --sin-registro  # prueba, no toca registry ni correlativo
python generar_oc.py datos.json --numero 1030   # re-emitir con un número específico
python generar_oc.py datos.json --forzar        # ignorar duplicado / totales que no cuadran
```

Requiere `playwright` (`pip install playwright && playwright install chromium`);
en el entorno de Claude ya viene instalado.

## Formato del JSON

Ver docstring de `generar_oc.py`. Claves: `empresa` (MAHUIDA/CAPITAL), `proveedor`
(debe existir en providers.csv), `nro_cotizacion`, `fecha_cotizacion`, `items[]`
(codigo, descripcion, cantidad, unidad, **precio_unitario neto con descuento aplicado**)
y `verificacion` (neto/iva/total que declara la cotización, para cruce automático).

## Garantías que el script viejo no tenía

- El correlativo se consume **después** de validar duplicados (no se queman números).
- Los totales calculados se cruzan contra los declarados en la cotización (tolerancia $2).
- Proveedor nuevo = una fila en `providers.csv`, cero código.
- Formato chileno de miles ($1.234.567) y decimales con coma.
- Sin límite de 18 ítems, sin Chrome portable, sin Tkinter.

## Proveedores verificados con cotizaciones reales

AISLACENTRO (reproduce la O.C. N°1030 exacta), COMERCIAL JONAS (descuentos y
descripciones multilínea), SODIMAC/HC (formato Reporte_Cotizacion), y los formatos
MCT y EBEMA quedan cubiertos porque Claude los lee directamente.

## Cotizaciones sin OC (seguimiento de precios)

```bash
python generar_oc.py datos.json --solo-precios
```
Registra los ítems en `registry.csv` con `nro_oc = -1`, sin PDF y sin consumir
correlativo. Si después se emite la OC de esa misma cotización, las filas `-1`
se reemplazan automáticamente por las de la OC (no quedan precios duplicados).
