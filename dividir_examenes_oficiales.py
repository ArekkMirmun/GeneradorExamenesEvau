"""
Divide los examenes oficiales de Selectividad en ejercicios individuales,
categorizados segun una referencia de ejercicios ya organizados.

Entrada:  Examenes/Matematicas_II/*.pdf  y  Examenes/Matematicas_CCSS/*.pdf
Salida:   ejercicios/CII/{categoria}/  y  ejercicios/CCSS/{categoria}/
"""

import os
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent
EXAMENES_DIR = BASE / "Examenes"
OUTPUT_DIR = BASE / "ejercicios"

# Ruta a los ejercicios de referencia ya categorizados
REF_DIR = Path(__file__).parent.parent / "RepoPrivado" / "ejercicios"

# Categorias conocidas (para parsear nombres con multi-palabra)
CII_CATS = ["funciones", "integrales", "geometria", "matrices", "sistemas",
            "distribucion", "probabilidad"]
CCSS_CATS = ["distribucion_binomial", "programacion_lineal", "teoria_muestras",
             "probabilidad", "matrices", "sistemas", "funciones"]

# ---------------------------------------------------------------------------
# Mapeo:  (year, periodo_ref) -> nombre_archivo_oficial (sin .pdf)
# ---------------------------------------------------------------------------
def _build_oficial_map():
    """Devuelve {asig: {year: {periodo: filename_stem}}}"""
    m = {}
    for asig in ["CII", "CCSS"]:
        m[asig] = {}
        for yr in range(2018, 2026):
            if yr <= 2019:
                m[asig][yr] = {
                    "junio": f"{yr}_titular_ordinaria",
                    "septiembre": f"{yr}_titular_extraordinaria",
                    "reserva1": f"{yr}_suplente_ordinaria",
                    "reserva2": f"{yr}_suplente_extraordinaria",
                    "reserva3": f"{yr}_reserva_a",
                    "reserva4": f"{yr}_reserva_b",
                }
            elif yr == 2020:
                if asig == "CII":
                    m[asig][yr] = {
                        "junio": f"{yr}_modelo_1",
                        "reserva1": f"{yr}_modelo_2",
                        "reserva2": f"{yr}_modelo_3",
                        "reserva3": f"{yr}_modelo_4",
                        "reserva4": f"{yr}_modelo_5",
                        "septiembre": f"{yr}_modelo_6",
                    }
                else:
                    m[asig][yr] = {
                        "junio": f"{yr}_modelo_a",
                        "reserva1": f"{yr}_modelo_b",
                        "reserva2": f"{yr}_modelo_c",
                        "reserva3": f"{yr}_modelo_d",
                        "reserva4": f"{yr}_modelo_e",
                        "septiembre": f"{yr}_modelo_f",
                    }
            elif yr <= 2022:
                m[asig][yr] = {
                    "junio": f"{yr}_titular_ordinaria",
                    "julio": f"{yr}_titular_extraordinaria",
                    "reserva1": f"{yr}_suplente_ordinaria",
                    "reserva2": f"{yr}_suplente_extraordinaria",
                    "reserva3": f"{yr}_reserva_a",
                    "reserva4": f"{yr}_reserva_b",
                }
            elif yr <= 2024:
                m[asig][yr] = {
                    "junio": f"{yr}_titular_a",
                    "julio": f"{yr}_titular_b",
                    "reserva1": f"{yr}_suplente_a",
                    "reserva2": f"{yr}_suplente_b",
                    "reserva3": f"{yr}_reserva_a",
                    "reserva4": f"{yr}_reserva_b",
                }
            else:  # 2025
                m[asig][yr] = {
                    "junio": f"{yr}_titular_a",
                    "julio": f"{yr}_titular_b",
                    "reserva1": f"{yr}_suplente1_a",
                    "reserva2": f"{yr}_suplente1_b",
                    "reserva3": f"{yr}_suplente2_a",
                    "reserva4": f"{yr}_suplente2_b",
                }
    return m

OFICIAL_MAP = _build_oficial_map()


# ---------------------------------------------------------------------------
# Construir referencia de categorias desde ejercicios organizados
# ---------------------------------------------------------------------------
def build_category_ref(ref_dir: Path):
    """
    Escanea los ejercicios de referencia y construye:
    {asig: {(year, periodo, exercise_num, opcion) -> category}}
    
    exercise_num: int (numero del ejercicio en el examen oficial)
    opcion: 'A', 'B', o None
    """
    ref = {"CII": {}, "CCSS": {}}
    
    for asig in ["CII", "CCSS"]:
        asig_dir = ref_dir / asig
        if not asig_dir.is_dir():
            continue
        cats = CII_CATS if asig == "CII" else CCSS_CATS
        
        for cat_dir in sorted(os.listdir(asig_dir)):
            cat_path = asig_dir / cat_dir
            if not cat_path.is_dir():
                continue
            
            for f in os.listdir(cat_path):
                if not f.endswith("_unsolved.pdf"):
                    continue
                name = f.replace("_unsolved.pdf", "")
                
                # Parsear: year_category_periodo_exerciseId[_opcionX]
                for c in cats:
                    prefix = f""
                    # Match year_category_
                    m = re.match(rf"^(\d{{4}})_{re.escape(c)}_(.+)$", name)
                    if not m:
                        continue
                    
                    year = int(m.group(1))
                    rest = m.group(2)  # periodo_exerciseId[_opcionX]
                    
                    # Extraer opcion si existe
                    opcion = None
                    m_op = re.search(r"_opcion([AB])$", rest)
                    if m_op:
                        opcion = m_op.group(1)
                        rest = rest[:m_op.start()]
                    
                    # Separar periodo y exerciseId
                    # rest = "junio_1" or "reserva1_A1" or "julio_7"
                    parts = rest.rsplit("_", 1)
                    if len(parts) != 2:
                        break
                    
                    periodo = parts[0]
                    ex_id = parts[1]
                    
                    # Extraer numero puro del exercise ID
                    # CII: "1", "5", etc.
                    # CCSS: "A1", "B3", "C5", "D7" -> extraer numero
                    m_num = re.search(r"(\d+)$", ex_id)
                    if not m_num:
                        break
                    ex_num = int(m_num.group(1))
                    
                    key = (year, periodo, ex_num, opcion)
                    ref[asig][key] = cat_dir
                    break
    
    return ref


# ---------------------------------------------------------------------------
# Invertir mapa: official_filename -> (periodo_ref, year)
# ---------------------------------------------------------------------------
def build_inverse_map():
    """Devuelve {asig: {official_stem: (year, periodo)}}"""
    inv = {"CII": {}, "CCSS": {}}
    for asig in ["CII", "CCSS"]:
        for yr, periodos in OFICIAL_MAP[asig].items():
            for periodo, stem in periodos.items():
                inv[asig][stem] = (yr, periodo)
    return inv


# ---------------------------------------------------------------------------
# Encontrar posiciones de ejercicios en una pagina
# ---------------------------------------------------------------------------
def find_exercise_positions(page):
    """
    Devuelve lista de (exercise_num, y_top, opcion_or_none) ordenada por y_top.
    Para formato 2019 con Opcion A/B, devuelve la opcion asociada.
    """
    blocks = page.get_text("dict")["blocks"]
    markers = []
    current_opcion = None
    
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            text = " ".join(span["text"] for span in line["spans"]).strip()
            y_top = line["bbox"][1]
            
            # Detectar "Opción A" / "Opción B" (solo para 2019)
            m_op = re.match(r"^Opci[óo]n\s+([AB])$", text, re.IGNORECASE)
            if m_op:
                current_opcion = m_op.group(1).upper()
                continue
            
            # Detectar "EJERCICIO N" o "Ejercicio N"
            m_ej = re.match(r"^(?:EJERCICIO|Ejercicio)\s+(\d+)", text)
            if m_ej:
                ex_num = int(m_ej.group(1))
                markers.append((ex_num, y_top, current_opcion))
    
    return markers


# ---------------------------------------------------------------------------
# Extraer un ejercicio como PDF individual
# ---------------------------------------------------------------------------
def extract_exercise(src_doc, page_idx, y_start, y_end, output_path):
    """Recorta la region del ejercicio y la guarda como PDF con margen extra."""
    page = src_doc[page_idx]
    page_rect = page.rect
    
    # Clip: desde y_start hasta y_end, ancho completo
    clip = fitz.Rect(page_rect.x0, y_start - 3, page_rect.x1, y_end)
    
    # Crear nuevo documento con margen superior e inferior extra
    pad_top = 45      # espacio para la cabecera que anade el generador
    pad_bottom = 30   # margen inferior de seguridad
    out_doc = fitz.open()
    new_w = clip.width
    new_h = clip.height + pad_top + pad_bottom
    new_page = out_doc.new_page(width=new_w, height=new_h)
    
    # Insertar la region recortada desplazada hacia abajo
    target_rect = fitz.Rect(0, pad_top, new_w, pad_top + clip.height)
    new_page.show_pdf_page(target_rect, src_doc, page_idx, clip=clip)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out_doc.save(str(output_path))
    out_doc.close()


# ---------------------------------------------------------------------------
# Procesar un examen oficial
# ---------------------------------------------------------------------------
def process_exam(exam_path, asig, year, periodo, cat_ref, output_dir, stats):
    """Procesa un examen oficial y extrae sus ejercicios categorizados."""
    doc = fitz.open(str(exam_path))
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        markers = find_exercise_positions(page)
        
        if not markers:
            continue
        
        for i, (ex_num, y_top, opcion) in enumerate(markers):
            # Determinar y_end
            if i + 1 < len(markers):
                y_end = markers[i + 1][1] - 3
            else:
                y_end = page.rect.height
            
            # Buscar categoria en la referencia
            # Probar con opcion primero, luego sin
            key_with_op = (year, periodo, ex_num, opcion)
            key_no_op = (year, periodo, ex_num, None)
            
            category = cat_ref[asig].get(key_with_op) or cat_ref[asig].get(key_no_op)
            
            if not category:
                print(f"  WARN: Sin categoria para {asig} {year}/{periodo} ej{ex_num} op{opcion}")
                stats["skipped"] += 1
                continue
            
            # Nombre del archivo de salida
            opcion_suffix = f"_opcion{opcion}" if opcion else ""
            filename = f"{year}_{category}_{periodo}_{ex_num}{opcion_suffix}_unsolved.pdf"
            out_path = output_dir / asig / category / filename
            
            if out_path.exists():
                os.remove(str(out_path))
                stats["replaced"] += 1
            
            extract_exercise(doc, page_idx, y_top, y_end, out_path)
            stats["extracted"] += 1
            print(f"  {filename}")
    
    doc.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== Dividir examenes oficiales en ejercicios categorizados ===\n")
    
    # 1. Construir referencia de categorias
    if not REF_DIR.is_dir():
        print(f"No se encuentra la carpeta de referencia: {REF_DIR}")
        print("Se necesita RepoPrivado/ejercicios/ para saber las categorias.")
        sys.exit(1)
    
    print("Cargando referencia de categorias...")
    cat_ref = build_category_ref(REF_DIR)
    for asig in ["CII", "CCSS"]:
        n = len(cat_ref[asig])
        print(f"  {asig}: {n} ejercicios de referencia")
    print()
    
    # 2. Construir mapa inverso
    inv_map = build_inverse_map()
    
    # 3. Procesar examenes oficiales
    asig_folders = {
        "CII": EXAMENES_DIR / "Matematicas_II",
        "CCSS": EXAMENES_DIR / "Matematicas_CCSS",
    }
    
    stats = {"extracted": 0, "skipped": 0, "existing": 0, "no_map": 0, "replaced": 0}
    
    for asig, folder in asig_folders.items():
        if not folder.is_dir():
            print(f"No se encuentra: {folder}")
            continue
        
        print(f"--- Procesando {asig} ---")
        
        for pdf_file in sorted(folder.glob("*.pdf")):
            stem = pdf_file.stem
            
            # Buscar en mapa inverso
            if stem not in inv_map[asig]:
                # Puede ser Tabla_Normal u otro archivo auxiliar
                continue
            
            year, periodo = inv_map[asig][stem]
            print(f"\n{pdf_file.name} -> {year}/{periodo}")
            
            process_exam(pdf_file, asig, year, periodo, cat_ref, OUTPUT_DIR, stats)
    
    print(f"\n=== Resumen ===")
    print(f"Ejercicios extraidos: {stats['extracted']}")
    print(f"Reemplazados: {stats['replaced']}")
    print(f"Sin categoria (saltados): {stats['skipped']}")


if __name__ == "__main__":
    main()
