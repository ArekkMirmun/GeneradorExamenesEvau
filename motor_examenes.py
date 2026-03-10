"""
Motor de generacion de examenes para CII y CCSS.
Modulo compartido entre la app publica y la privada.
"""

import os
import re
import random
from datetime import date
from pathlib import Path

import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Estructura de temas por asignatura
# ---------------------------------------------------------------------------
CII_TEMAS = {
    "funciones": "Funciones",
    "integrales": "Integrales",
    "geometria": "Geometria",
    "matrices": "Matrices",
    "sistemas": "Sistemas",
    "distribucion": "Distribucion",
    "probabilidad": "Probabilidad",
}

CCSS_TEMAS = {
    "matrices": "Matrices",
    "sistemas": "Sistemas",
    "programacion_lineal": "Prog. Lineal",
    "funciones": "Funciones",
    "probabilidad": "Probabilidad",
    "teoria_muestras": "Teoria Muestras",
    "distribucion_binomial": "Dist. Binomial",
}

# Estructura oficial del examen CII (2025)
CII_UNITS = {
    "analisis": ["funciones", "integrales"],
    "algebra": ["matrices", "sistemas"],
    "geometria": ["geometria"],
}
CII_ESTADISTICA = ["distribucion", "probabilidad"]

# Estructura oficial del examen CCSS (2025)
# Ej1 (3pts): A1+C2+C3 -> matrices + funciones
# Ej2 (3pts): B1+B2+C4 -> programacion_lineal + sistemas
# Ej3-4 (2pts): D1+D2+D3 -> probabilidad + teoria_muestras + distribucion_binomial
CCSS_GROUPS = {
    "algebra_funciones": ["matrices", "funciones"],
    "programacion_sistemas": ["programacion_lineal", "sistemas"],
    "estadistica": ["probabilidad", "teoria_muestras", "distribucion_binomial"],
}


# ---------------------------------------------------------------------------
# Carga de ejercicios
# ---------------------------------------------------------------------------
def load_exercises(exercises_dir: Path):
    """Carga ejercicios agrupados por asignatura y tema.
    Returns: {"CII": {"funciones": [...], ...}, "CCSS": {"matrices": [...], ...}}
    """
    result = {}
    for asig in ["CII", "CCSS"]:
        asig_dir = exercises_dir / asig
        if not asig_dir.is_dir():
            continue
        result[asig] = {}
        for tema in sorted(os.listdir(asig_dir)):
            tema_dir = asig_dir / tema
            if not tema_dir.is_dir():
                continue
            unsolved = sorted(str(f) for f in tema_dir.glob("*_unsolved.pdf"))
            if unsolved:
                result[asig][tema] = unsolved
    return result


def get_available_temas(exercises):
    """Devuelve los temas disponibles con conteo."""
    info = {}
    for asig in ["CII", "CCSS"]:
        temas_map = CII_TEMAS if asig == "CII" else CCSS_TEMAS
        if asig not in exercises:
            continue
        info[asig] = {}
        for tema_key, tema_display in temas_map.items():
            count = len(exercises[asig].get(tema_key, []))
            if count > 0:
                info[asig][tema_key] = {"display": tema_display, "count": count}
    return info


# ---------------------------------------------------------------------------
# Generacion de examenes
# ---------------------------------------------------------------------------
def _pick(pool, n, used):
    """Selecciona n ejercicios aleatorios del pool que no esten en used."""
    available = [f for f in pool if f not in used]
    if len(available) < n:
        raise ValueError(f"Insuficientes ejercicios (hay {len(available)}, necesita {n})")
    selected = random.sample(available, n)
    used.update(selected)
    return selected


def generate_cii_exam(exercises, temas_activos, seed=None):
    """Genera un examen CII con estructura oficial.
    - 1 ej analisis obligatorio
    - 1 ej obligatorio de otra unidad
    - Bloque1: 2 ej de una unidad
    - Bloque2: 1 estadistica + 1 de otra unidad
    """
    if seed is not None:
        random.seed(seed)

    used = set()

    # Pool filtrado por temas activos
    pools = {}
    for tema in temas_activos:
        files = exercises.get("CII", {}).get(tema, [])
        if files:
            pools[tema] = files

    # Componer los pools por unidad filtrados
    unit_pools = {}
    for unit_name, cats in CII_UNITS.items():
        pool = []
        for cat in cats:
            if cat in pools:
                pool.extend(pools[cat])
        if pool:
            unit_pools[unit_name] = pool

    est_pool = []
    for cat in CII_ESTADISTICA:
        if cat in pools:
            est_pool.extend(pools[cat])

    # Si no hay suficientes unidades, genera mixto
    available_units = list(unit_pools.keys())
    if len(available_units) < 2:
        return _generate_mixed(exercises, "CII", temas_activos, 6, seed)

    random.shuffle(available_units)

    # Ej1: analisis obligatorio (si disponible)
    if "analisis" in unit_pools:
        ej1 = _pick(unit_pools["analisis"], 1, used)
        other_units = [u for u in available_units if u != "analisis"]
    else:
        ej1 = _pick(unit_pools[available_units[0]], 1, used)
        other_units = [u for u in available_units if u != available_units[0]]

    # Ej2: otra unidad obligatoria
    if other_units:
        unit_oblig = other_units[0]
        ej2 = _pick(unit_pools[unit_oblig], 1, used)
        remaining_units = other_units[1:]
    else:
        ej2 = _pick(unit_pools[available_units[-1]], 1, used)
        remaining_units = []

    # Bloque1: 2 ej de una unidad
    bloque1 = []
    if remaining_units and len([f for f in unit_pools.get(remaining_units[0], []) if f not in used]) >= 2:
        bloque1 = _pick(unit_pools[remaining_units[0]], 2, used)
    else:
        # Fallback: any available
        all_remaining = []
        for u in available_units:
            all_remaining.extend(f for f in unit_pools[u] if f not in used)
        if len(all_remaining) >= 2:
            bloque1 = random.sample(all_remaining, 2)
            used.update(bloque1)

    # Bloque2: 1 estadistica + 1 de otra unidad
    bloque2 = []
    if est_pool:
        est_avail = [f for f in est_pool if f not in used]
        if est_avail:
            est_pick = random.sample(est_avail, 1)
            used.update(est_pick)
            bloque2.extend(est_pick)

    # Fill remaining from any pool
    all_avail = []
    for tema in temas_activos:
        all_avail.extend(f for f in pools.get(tema, []) if f not in used)
    needed = 6 - len(ej1) - len(ej2) - len(bloque1) - len(bloque2)
    if needed > 0 and len(all_avail) >= needed:
        extra = random.sample(all_avail, needed)
        used.update(extra)
        bloque2.extend(extra)

    sections = {
        "obligatoria": ej1 + ej2,
        "bloque1": bloque1,
        "bloque2": bloque2,
    }
    labels = {
        "obligatoria": "PARTE OBLIGATORIA",
        "bloque1": "BLOQUE OPTATIVO 1",
        "bloque2": "BLOQUE OPTATIVO 2",
    }
    return sections, labels


def generate_ccss_exam(exercises, temas_activos, seed=None):
    """Genera un examen CCSS con estructura oficial.
    - Ej1 (3pts): matrices/funciones
    - Ej2 (3pts): prog_lineal/sistemas
    - Ej3-4 (2pts): probabilidad/teoria_muestras/dist_binomial
    """
    if seed is not None:
        random.seed(seed)

    used = set()
    pools = {}
    for tema in temas_activos:
        files = exercises.get("CCSS", {}).get(tema, [])
        if files:
            pools[tema] = files

    # Group pools
    g1 = []
    for cat in CCSS_GROUPS["algebra_funciones"]:
        g1.extend(pools.get(cat, []))
    g2 = []
    for cat in CCSS_GROUPS["programacion_sistemas"]:
        g2.extend(pools.get(cat, []))
    g3 = []
    for cat in CCSS_GROUPS["estadistica"]:
        g3.extend(pools.get(cat, []))

    # If not enough for structure, go mixed
    if not g1 or not g2 or not g3:
        return _generate_mixed(exercises, "CCSS", temas_activos, 4, seed)

    ej1 = _pick(g1, 1, used)
    ej2 = _pick(g2, 1, used)
    ej34 = _pick(g3, min(2, len([f for f in g3 if f not in used])), used)

    sections = {
        "ej1_algebra_funciones": ej1,
        "ej2_prog_sistemas": ej2,
        "ej3_4_estadistica": ej34,
    }
    labels = {
        "ej1_algebra_funciones": "EJERCICIO 1 (3 puntos) - Algebra/Funciones",
        "ej2_prog_sistemas": "EJERCICIO 2 (3 puntos) - Prog. Lineal/Sistemas",
        "ej3_4_estadistica": "EJERCICIOS 3-4 (2 puntos c/u) - Estadistica",
    }
    return sections, labels


def _generate_mixed(exercises, asig, temas_activos, n, seed=None):
    """Genera un examen mixto con N ejercicios aleatorios."""
    if seed is not None:
        random.seed(seed)
    pool = []
    for tema in temas_activos:
        pool.extend(exercises.get(asig, {}).get(tema, []))
    if len(pool) < n:
        n = len(pool)
    selected = random.sample(pool, n)
    sections = {"ejercicios": selected}
    labels = {"ejercicios": "EJERCICIOS"}
    return sections, labels


def generate_mixed_both_exam(exercises, temas_cii, temas_ccss, n=6, seed=None):
    """Genera un examen mezclado con ejercicios de CII y CCSS."""
    if seed is not None:
        random.seed(seed)
    pool_cii = []
    for tema in temas_cii:
        pool_cii.extend(exercises.get("CII", {}).get(tema, []))
    pool_ccss = []
    for tema in temas_ccss:
        pool_ccss.extend(exercises.get("CCSS", {}).get(tema, []))
    pool = pool_cii + pool_ccss
    if len(pool) < n:
        n = len(pool)
    selected = random.sample(pool, n)
    sections = {"ejercicios": selected}
    labels = {"ejercicios": "EJERCICIOS (CII + CCSS)"}
    return sections, labels


def get_next_exam_id(output_dir):
    """Devuelve el siguiente ID de examen basado en los existentes."""
    out = Path(output_dir)
    if not out.is_dir():
        return 1
    max_id = 0
    for f in out.glob("Examen_*.pdf"):
        m = re.search(r"Examen_\w+_(\d+)", f.stem)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return max_id + 1


# ---------------------------------------------------------------------------
# Construccion del PDF
# ---------------------------------------------------------------------------
def build_exam_pdf(sections, labels, exam_id, output_dir, asig_tag, solved=False):
    """Construye el PDF del examen.

    asig_tag: "CII", "CCSS", or "CII_y_CCSS"
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = "_resuelto" if solved else ""
    filename = f"Examen_{asig_tag}_{exam_id}{suffix}.pdf"
    out_path = out_dir / filename

    doc = fitz.open()
    font_bold = fitz.Font("helv")
    font_normal = fitz.Font("helv")

    # Title
    asig_display = {
        "CII": "MATEMATICAS II",
        "CCSS": "MATEMATICAS CCSS",
        "CII_y_CCSS": "MATEMATICAS II + CCSS",
    }.get(asig_tag, asig_tag)

    # --- Cover page ---
    cover = doc.new_page(width=595, height=842)
    tw = fitz.TextWriter(cover.rect)
    tw.append((120, 80), asig_display, font=font_bold, fontsize=20)
    tw.append((200, 115), f"EXAMEN {exam_id}", font=font_bold, fontsize=16)
    if solved:
        tw.append((220, 145), "VERSION RESUELTA", font=font_bold, fontsize=12)

    y = 180
    exercise_num = 1
    for sec_key in sections:
        y += 20
        tw.append((50, y), labels[sec_key], font=font_bold, fontsize=12)
        y += 5
        for ex_path in sections[sec_key]:
            name = Path(ex_path).stem.replace("_unsolved", "").replace("_solved", "")
            y += 18
            tw.append((70, y), f"Ejercicio {exercise_num}: {name}",
                       font=font_normal, fontsize=10)
            exercise_num += 1

    tw.write_text(cover)

    A4_W, A4_H = 595, 842
    MARGIN = 40  # horizontal margin for exercise content on A4

    # --- Exercise pages ---
    exercise_num = 1
    for sec_key in sections:
        for ex_path in sections[sec_key]:
            if solved:
                ex_path = ex_path.replace("_unsolved.pdf", "_solved.pdf")

            if not Path(ex_path).exists():
                continue

            ex_doc = fitz.open(ex_path)
            for pi in range(len(ex_doc)):
                src_page = ex_doc[pi]
                src_w = src_page.rect.width
                src_h = src_page.rect.height

                # Create A4 page
                new_page = doc.new_page(width=A4_W, height=A4_H)

                # Available area for content
                header_h = 35 if pi == 0 else 0
                content_area_w = A4_W - 2 * MARGIN
                content_area_h = A4_H - header_h - MARGIN  # top offset + bottom margin

                # Scale to fit A4 while preserving aspect ratio
                scale = min(content_area_w / src_w, content_area_h / src_h, 1.0)
                dst_w = src_w * scale
                dst_h = src_h * scale

                # Center horizontally
                x0 = (A4_W - dst_w) / 2
                y0 = header_h
                target = fitz.Rect(x0, y0, x0 + dst_w, y0 + dst_h)
                new_page.show_pdf_page(target, ex_doc, pi)

                if pi == 0:
                    # Draw header
                    tw2 = fitz.TextWriter(new_page.rect)
                    tw2.append((MARGIN, 22),
                               f"Ejercicio {exercise_num} - {labels[sec_key]}",
                               font=font_bold, fontsize=9)
                    tw2.write_text(new_page)
            ex_doc.close()
            exercise_num += 1

    doc.save(str(out_path))
    doc.close()
    return str(out_path)
