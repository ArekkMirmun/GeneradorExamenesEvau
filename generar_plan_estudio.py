"""
Generador de plan de estudio diario - Selectividad
Distribuye los examenes de Examenes/ en un plan dia a dia.

Cada dia se asigna un examen completo para practicar.
Se alternan las asignaturas y se mezclan los annos.
"""

import os
import random
from datetime import date, timedelta
from pathlib import Path

import fitz  # PyMuPDF

BASE = Path(__file__).parent
EXAMENES_DIR = BASE / "Examenes"
OUTPUT_DIR = BASE / "plan_diario"

FECHA_INICIO = date(2026, 3, 9)
FECHA_FIN = date(2026, 6, 1)


def load_exams():
    """Carga todos los examenes organizados por asignatura."""
    exams = {}
    for asig in sorted(os.listdir(EXAMENES_DIR)):
        asig_path = EXAMENES_DIR / asig
        if not asig_path.is_dir():
            continue
        files = sorted(str(f) for f in asig_path.glob("*.pdf"))
        if files:
            exams[asig] = files
    return exams


def distribute_exams(exams, num_days):
    """
    Distribuye los examenes alternando asignaturas dia a dia.
    Asigna ~1 examen por dia, alternando Mat II / CCSS.
    Si hay mas dias que examenes, se rellenan con repeticiones aleatorias.
    """
    plan = [[] for _ in range(num_days)]

    # Crear pool intercalado: Mat II, CCSS, Mat II, CCSS...
    asignaturas = sorted(exams.keys())
    pools = {}
    for asig in asignaturas:
        pool = list(exams[asig])
        random.shuffle(pool)
        pools[asig] = pool

    # Intercalar
    sequence = []
    max_len = max(len(p) for p in pools.values())
    for i in range(max_len):
        for asig in asignaturas:
            if i < len(pools[asig]):
                sequence.append((asig, pools[asig][i]))

    # Asignar a dias
    for i, (asig, exam) in enumerate(sequence):
        day = i % num_days
        plan[day].append((asig, exam))

    return plan


def build_daily_pdf(day_exercises, day_num, day_date):
    """Genera el PDF de un dia con su examen asignado."""
    out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"dia_{day_num:03d}_{day_date.strftime('%Y-%m-%d')}.pdf"
    out_path = out_dir / filename

    doc = fitz.open()
    font_bold = fitz.Font("helv")
    font_normal = fitz.Font("helv")

    # --- Portada ---
    cover = doc.new_page(width=595, height=842)
    tw = fitz.TextWriter(cover.rect)
    tw.append((120, 80), "PLAN DE ESTUDIO DIARIO", font=font_bold, fontsize=18)
    tw.append((200, 115), f"Dia {day_num} - {day_date.strftime('%d/%m/%Y')}",
              font=font_bold, fontsize=14)

    day_names = {0: "Lunes", 1: "Martes", 2: "Miercoles",
                 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"}
    tw.append((230, 140), day_names[day_date.weekday()],
              font=font_normal, fontsize=12)

    y = 180
    tw.append((50, y), f"Examenes del dia: {len(day_exercises)}",
              font=font_bold, fontsize=12)

    for asig, exam_path in day_exercises:
        y += 25
        name = Path(exam_path).stem
        display_asig = asig.replace("_", " ")
        tw.append((70, y), f"{display_asig}: {name}",
                  font=font_normal, fontsize=10)

    tw.write_text(cover)

    # --- Paginas de examenes ---
    for asig, exam_path in day_exercises:
        # Insertar separador con nombre
        sep = doc.new_page(width=595, height=842)
        tw2 = fitz.TextWriter(sep.rect)
        name = Path(exam_path).stem
        display_asig = asig.replace("_", " ").upper()
        tw2.append((150, 400), display_asig, font=font_bold, fontsize=24)
        tw2.append((180, 440), name, font=font_normal, fontsize=16)
        tw2.write_text(sep)

        # Insertar paginas del examen
        ex_doc = fitz.open(exam_path)
        for pi in range(len(ex_doc)):
            doc.insert_pdf(ex_doc, from_page=pi, to_page=pi)
        ex_doc.close()

    # Adjuntar Tabla Normal si alguno es CCSS
    has_ccss = any("CCSS" in asig for asig, _ in day_exercises)
    tabla_path = EXAMENES_DIR / "Tabla_Normal.pdf"
    if has_ccss and tabla_path.exists():
        tabla_doc = fitz.open(str(tabla_path))
        doc.insert_pdf(tabla_doc)
        tabla_doc.close()

    doc.save(str(out_path))
    doc.close()
    return str(out_path)


def main():
    random.seed(42)

    num_days = (FECHA_FIN - FECHA_INICIO).days + 1
    print(f"Periodo: {FECHA_INICIO} -> {FECHA_FIN} ({num_days} dias)")

    exams = load_exams()
    total = sum(len(v) for v in exams.values())
    print(f"Examenes totales: {total}")
    for asig, files in sorted(exams.items()):
        print(f"  {asig}: {len(files)}")

    plan = distribute_exams(exams, num_days)

    counts = [len(day) for day in plan]
    non_empty = [c for c in counts if c > 0]
    print(f"\nDistribucion:")
    print(f"  Dias con examen: {len(non_empty)}/{num_days}")
    print(f"  Examenes/dia: {min(non_empty)}-{max(non_empty)}")
    print(f"  Total asignados: {sum(counts)}")

    print(f"\nGenerando PDFs en '{OUTPUT_DIR}'...")
    generated = 0
    for i, day_exercises in enumerate(plan):
        day_date = FECHA_INICIO + timedelta(days=i)
        day_num = i + 1
        if not day_exercises:
            continue
        build_daily_pdf(day_exercises, day_num, day_date)
        generated += 1
        if generated % 10 == 0:
            print(f"  Generados: {generated}")

    print(f"\nCompletado: {generated} dias con examenes generados en '{OUTPUT_DIR}'")

    print("\n--- RESUMEN DEL PLAN ---")
    for i, day_exercises in enumerate(plan):
        day_date = FECHA_INICIO + timedelta(days=i)
        day_num = i + 1
        if not day_exercises:
            exams_str = "(descanso)"
        else:
            exams_str = ", ".join(
                f"{Path(e).stem} [{a.replace('Matematicas_', '')}]"
                for a, e in day_exercises
            )
        wd = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"][day_date.weekday()]
        print(f"  Dia {day_num:3d} ({day_date.strftime('%d/%m')} {wd}): {exams_str}")


if __name__ == "__main__":
    main()
