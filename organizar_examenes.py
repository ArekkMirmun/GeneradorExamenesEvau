"""
organizar_examenes.py
Recorre ExamenesOriginales/ (estructura desordenada) y genera una carpeta
Examenes/ con nombres y estructura uniformes.

- Detecta asignatura (Matematicas II / Matematicas CCSS)
- Extrae anno y convocatoria de la ruta y nombre de archivo
- Elimina paginas de criterios de correccion
- Elimina archivos que no son examenes (Tabla Normal, .edi, archivos ._*)
- Guarda una copia maestra de la Tabla Normal (util para CCSS y 2025 Mat II)

Estructura de salida:
    Examenes/
        Matematicas_II/
            2018_titular_junio.pdf
            2018_titular_septiembre.pdf
            ...
        Matematicas_CCSS/
            2018_titular_junio.pdf
            ...
        Tabla_Normal.pdf
"""

import os
import re
import shutil
from pathlib import Path

import fitz  # PyMuPDF

BASE = Path(__file__).parent
INPUT_DIR = BASE / "ExamenesOriginales"
OUTPUT_DIR = BASE / "Examenes"
TABLA_OUTPUT = OUTPUT_DIR / "Tabla_Normal.pdf"

# ── helpers ──────────────────────────────────────────────────────────────

def es_tabla(filename: str) -> bool:
    low = filename.lower()
    if low.startswith("tabla"):
        return True
    return "tabla" in low and ("normal" in low or "n(0,1)" in low or "distribuci" in low)


def es_criterios_page(page) -> bool:
    text = page.get_text()[:500].upper()
    return "CRITERIOS" in text and "CORRECCI" in text


def detectar_asignatura(ruta: str) -> str:
    """Devuelve 'Matematicas_II' o 'Matematicas_CCSS'."""
    low = ruta.lower()
    if "ccss" in low or "aplicad" in low or "ciencias sociales" in low:
        return "Matematicas_CCSS"
    return "Matematicas_II"


def extraer_anno(ruta: str) -> str:
    """Extrae el anno a partir de sel_XXXX_ en la ruta."""
    m = re.search(r"sel_(\d{4})", ruta)
    return m.group(1) if m else "0000"


# ── Mapping de convocatoria ──────────────────────────────────────────────
# Cubre todas las variantes observadas en 2018-2025

CONV_MAP = {
    # Desde nombre de carpeta (2018-2019)
    "titular_junio":          "titular_ordinaria",
    "titular junio":          "titular_ordinaria",
    "titular_septiembre":     "titular_extraordinaria",
    "titular septiembre":     "titular_extraordinaria",
    "reserva a":              "reserva_a",
    "reserva b":              "reserva_b",
    "suplente junio":         "suplente_ordinaria",
    "suplente septiembre":    "suplente_extraordinaria",
    # Desde prefijo de filename (2021-2022)
    "ord_titular":            "titular_ordinaria",
    "ord_reser":              "reserva_a",
    "ord_reserva":            "reserva_a",
    "ord_suplente":           "suplente_ordinaria",
    "extra_titular":          "titular_extraordinaria",
    "extra_reserva_b":        "reserva_b",
    "extra_reserva":          "reserva_b",
    "extra_suplente":         "suplente_extraordinaria",
    # Desde filename (2022)
    "ord-titular":            "titular_ordinaria",
    "ord-reserva":            "reserva_a",
    "ord-suplente":           "suplente_ordinaria",
    "extra-titular":          "titular_extraordinaria",
    "extra-reserva":          "reserva_b",
    "extra-suplente":         "suplente_extraordinaria",
    # Desde filename (2023-2024)
    "titular-a":              "titular_a",
    "titular-b":              "titular_b",
    "reserva-a":              "reserva_a",
    "reserva-b":              "reserva_b",
    "suplente-a":             "suplente_a",
    "suplente-b":             "suplente_b",
    "titular a":              "titular_a",
    "titular b":              "titular_b",
    "reserva a":              "reserva_a",
    "reserva b":              "reserva_b",
    "suplente a":             "suplente_a",
    "suplente b":             "suplente_b",
    # Desde filename (2025)
    "suplente1-a":            "suplente1_a",
    "suplente1-b":            "suplente1_b",
    "suplente2-a":            "suplente2_a",
    "suplente2-b":            "suplente2_b",
}


def extraer_convocatoria(ruta_completa: str, filename: str, anno: str) -> str:
    """Intenta extraer la convocatoria del filename o de las carpetas padre."""
    low_path = ruta_completa.lower().replace("\\", "/")
    low_name = filename.lower()

    # 2020 formato especial: matematicas_Examen_N / matematicas_aplicadas_C_A
    if anno == "2020":
        # Mat II: matematicas_Examen_1..6
        m = re.search(r"examen[_\s]*(\d)", low_name)
        if m:
            return f"modelo_{m.group(1)}"
        # CCSS: matematicas_aplicadas_{C|P}_{A..F}  (C=Criterios, P=Prueba)
        m = re.search(r"aplicadas?_([cp])_([a-f])", low_name)
        if m:
            if m.group(1) == "c":
                return None  # Criterios, no es examen
            return f"modelo_{m.group(2)}"
        return "desconocido"

    # Intentar match con CONV_MAP desde filename
    for key, val in sorted(CONV_MAP.items(), key=lambda x: -len(x[0])):
        if key in low_name:
            return val

    # Intentar match con carpetas padre
    parts = low_path.split("/")
    for part in parts:
        for key, val in sorted(CONV_MAP.items(), key=lambda x: -len(x[0])):
            if key == part or key == part.strip():
                return val

    return "desconocido"


def procesar_examen(src_path: str, dst_path: str):
    """Copia el examen eliminando paginas de criterios."""
    doc = fitz.open(src_path)
    pages_to_keep = []
    for i in range(len(doc)):
        if not es_criterios_page(doc[i]):
            # Tambien descartar paginas en blanco (< 20 chars de texto)
            text = doc[i].get_text().strip()
            if len(text) > 20:
                pages_to_keep.append(i)

    if not pages_to_keep:
        doc.close()
        return False

    out = fitz.open()
    for pi in pages_to_keep:
        out.insert_pdf(doc, from_page=pi, to_page=pi)

    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    out.save(dst_path)
    out.close()
    doc.close()
    return True


def main():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    tabla_saved = False
    stats = {"examenes": 0, "tablas": 0, "criterios_pages": 0,
             "ignorados": 0, "errores": 0}

    for root, dirs, files in os.walk(INPUT_DIR):
        for fname in sorted(files):
            src = os.path.join(root, fname)
            rel = os.path.relpath(src, INPUT_DIR)

            # Ignorar archivos ocultos de macOS, .edi, etc
            if fname.startswith(".") or fname.startswith("._"):
                stats["ignorados"] += 1
                continue
            if not fname.lower().endswith(".pdf"):
                stats["ignorados"] += 1
                print(f"  [SKIP] No es PDF: {rel}")
                continue

            # Detectar Tabla Normal
            if es_tabla(fname):
                stats["tablas"] += 1
                if not tabla_saved:
                    try:
                        doc = fitz.open(src)
                        doc.save(str(TABLA_OUTPUT))
                        doc.close()
                        tabla_saved = True
                        print(f"  [TABLA] Guardada: {rel}")
                    except Exception:
                        pass
                else:
                    print(f"  [TABLA] Duplicado ignorado: {rel}")
                continue

            # Es un examen
            asignatura = detectar_asignatura(rel)
            anno = extraer_anno(rel)
            conv = extraer_convocatoria(rel, fname, anno)

            if conv is None:
                stats["ignorados"] += 1
                print(f"  [SKIP] Criterios: {rel}")
                continue

            out_name = f"{anno}_{conv}.pdf"
            out_path = OUTPUT_DIR / asignatura / out_name

            # Evitar colisiones
            if out_path.exists():
                base_name = out_path.stem
                i = 2
                while out_path.exists():
                    out_path = OUTPUT_DIR / asignatura / f"{base_name}_{i}.pdf"
                    i += 1

            try:
                doc = fitz.open(src)
                orig_pages = len(doc)
                doc.close()

                ok = procesar_examen(src, str(out_path))
                if ok:
                    doc2 = fitz.open(str(out_path))
                    new_pages = len(doc2)
                    doc2.close()
                    removed = orig_pages - new_pages
                    stats["criterios_pages"] += removed
                    stats["examenes"] += 1
                    extra = f" (eliminadas {removed} pag de criterios)" if removed else ""
                    print(f"  [OK] {out_path.name}{extra}")
                else:
                    stats["errores"] += 1
                    print(f"  [ERR] Sin paginas utiles: {rel}")
            except Exception as e:
                stats["errores"] += 1
                print(f"  [ERR] {rel}: {e}")

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    for asig in sorted(os.listdir(OUTPUT_DIR)):
        asig_path = OUTPUT_DIR / asig
        if asig_path.is_dir():
            n = len(list(asig_path.glob("*.pdf")))
            print(f"  {asig}: {n} examenes")

    print(f"\n  Examenes procesados: {stats['examenes']}")
    print(f"  Paginas de criterios eliminadas: {stats['criterios_pages']}")
    print(f"  Tablas Normal encontradas: {stats['tablas']} (1 guardada)")
    print(f"  Archivos ignorados: {stats['ignorados']}")
    print(f"  Errores: {stats['errores']}")

    if tabla_saved:
        print(f"\n  Tabla Normal guardada en: {TABLA_OUTPUT}")


if __name__ == "__main__":
    main()
