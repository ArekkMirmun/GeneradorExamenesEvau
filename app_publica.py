"""
Generador de Examenes Selectividad - Version PUBLICA
Genera examenes aleatorios SIN soluciones.
"""

import os
import sys
import random
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import date

import fitz  # PyMuPDF

# Import engine - handle both script and frozen modes
if getattr(sys, "frozen", False):
    _base = Path(sys.executable).parent
    sys.path.insert(0, str(_base))
else:
    _base = Path(__file__).parent

from motor_examenes import (
    load_exercises, get_available_temas, generate_cii_exam,
    generate_ccss_exam, _generate_mixed, generate_mixed_both_exam,
    build_exam_pdf, get_next_exam_id,
    CII_TEMAS, CCSS_TEMAS,
)

BASE_PATH = _base


class ExamApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generador de Examenes Selectividad")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        icon_path = BASE_PATH / "icon.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))

        self._exercises = {}
        self._tema_vars = {}
        self._build_ui()
        self._center_window()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 4}

        # Header
        hdr = tk.Frame(self, bg="#1a237e", height=60)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Generador de Examenes Selectividad",
                 font=("Segoe UI", 16, "bold"), fg="white", bg="#1a237e"
                 ).pack(pady=6)
        tk.Label(hdr, text="Version publica (sin soluciones)",
                 font=("Segoe UI", 9), fg="#b0bec5", bg="#1a237e"
                 ).pack()

        main = tk.Frame(self, bg="#f0f0f0")
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # --- Carpeta ejercicios ---
        row = 0
        tk.Label(main, text="Carpeta de ejercicios:", bg="#f0f0f0",
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", **pad)
        self.var_ex_dir = tk.StringVar(value=str(BASE_PATH / "ejercicios"))
        tk.Entry(main, textvariable=self.var_ex_dir, width=45,
                 font=("Segoe UI", 9)).grid(row=row, column=1, sticky="ew", **pad)
        tk.Button(main, text="...", width=3,
                  command=lambda: self._browse("var_ex_dir")).grid(row=row, column=2, **pad)

        # --- Asignatura ---
        row += 1
        tk.Label(main, text="Asignatura:", bg="#f0f0f0",
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", **pad)
        self.var_asig = tk.StringVar(value="CII_y_CCSS")
        asig_frame = tk.Frame(main, bg="#f0f0f0")
        asig_frame.grid(row=row, column=1, sticky="w", **pad)
        for val, txt in [("CII", "Mat. II"), ("CCSS", "Mat. CCSS"), ("CII_y_CCSS", "Ambas")]:
            tk.Radiobutton(asig_frame, text=txt, variable=self.var_asig, value=val,
                           bg="#f0f0f0", font=("Segoe UI", 9),
                           command=self._on_asig_change).pack(side="left", padx=6)

        # --- Temas (checkboxes) ---
        row += 1
        tk.Label(main, text="Temas:", bg="#f0f0f0",
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="nw", **pad)
        self.temas_frame = tk.Frame(main, bg="#f0f0f0")
        self.temas_frame.grid(row=row, column=1, columnspan=2, sticky="w", **pad)

        # --- Num examenes ---
        row += 1
        tk.Label(main, text="Numero de examenes:", bg="#f0f0f0",
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", **pad)
        self.var_num = tk.IntVar(value=1)
        ttk.Spinbox(main, from_=1, to=100, textvariable=self.var_num,
                     width=8, font=("Segoe UI", 10)).grid(row=row, column=1, sticky="w", **pad)

        # --- Seed ---
        row += 1
        tk.Label(main, text="Semilla (vacio = aleatorio):", bg="#f0f0f0",
                 font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", **pad)
        self.var_seed = tk.StringVar()
        tk.Entry(main, textvariable=self.var_seed, width=15,
                 font=("Segoe UI", 10)).grid(row=row, column=1, sticky="w", **pad)

        # --- Separator ---
        row += 1
        ttk.Separator(main, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=8)

        # --- Status ---
        row += 1
        self.lbl_status = tk.Label(main, text="Estado: ejercicios no cargados",
                                   bg="#f0f0f0", fg="#757575",
                                   font=("Segoe UI", 9), anchor="w")
        self.lbl_status.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)

        # --- Progress ---
        row += 1
        self.progress = ttk.Progressbar(main, length=400, mode="determinate")
        self.progress.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)

        # --- Buttons ---
        row += 1
        btn_frame = tk.Frame(main, bg="#f0f0f0")
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)

        self.btn_load = tk.Button(
            btn_frame, text="Cargar ejercicios", font=("Segoe UI", 10, "bold"),
            bg="#4caf50", fg="white", width=18, command=self._load)
        self.btn_load.pack(side="left", padx=8)

        self.btn_gen = tk.Button(
            btn_frame, text="Generar examenes", font=("Segoe UI", 10, "bold"),
            bg="#1a237e", fg="white", width=18, command=self._start_gen,
            state="disabled")
        self.btn_gen.pack(side="left", padx=8)

        self.btn_open = tk.Button(
            btn_frame, text="Abrir carpeta", font=("Segoe UI", 10),
            width=14, command=self._open_folder, state="disabled")
        self.btn_open.pack(side="left", padx=8)

        # --- Log ---
        row += 1
        tk.Label(main, text="Registro:", bg="#f0f0f0",
                 font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", **pad)
        row += 1
        self.log_text = tk.Text(main, height=10, width=70, font=("Consolas", 9),
                                bg="white", state="disabled", wrap="word")
        self.log_text.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        sb = ttk.Scrollbar(main, orient="vertical", command=self.log_text.yview)
        sb.grid(row=row, column=3, sticky="ns")
        self.log_text.configure(yscrollcommand=sb.set)

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def _set_status(self, msg, color="#757575"):
        self.lbl_status.configure(text=f"Estado: {msg}", fg=color)
        self.update_idletasks()

    def _browse(self, var_name):
        d = filedialog.askdirectory()
        if d:
            getattr(self, var_name).set(d)

    def _on_asig_change(self):
        if self._exercises:
            self._update_temas()

    def _update_temas(self):
        for w in self.temas_frame.winfo_children():
            w.destroy()
        self._tema_vars.clear()

        info = get_available_temas(self._exercises)
        asig = self.var_asig.get()

        asigs = []
        if asig in ("CII", "CII_y_CCSS"):
            asigs.append("CII")
        if asig in ("CCSS", "CII_y_CCSS"):
            asigs.append("CCSS")

        for col_idx, a in enumerate(asigs):
            if a not in info:
                continue
            col_frame = tk.Frame(self.temas_frame, bg="#f0f0f0")
            col_frame.grid(row=0, column=col_idx, sticky="nw", padx=(0, 24))
            lbl = "Mat. II" if a == "CII" else "Mat. CCSS"
            tk.Label(col_frame, text=f"{lbl}:", bg="#f0f0f0",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            for tema_key, tema_info in info[a].items():
                var = tk.BooleanVar(value=True)
                key = f"{a}_{tema_key}"
                self._tema_vars[key] = var
                tk.Checkbutton(
                    col_frame,
                    text=f"  {tema_info['display']} ({tema_info['count']})",
                    variable=var, bg="#f0f0f0", font=("Segoe UI", 9)
                ).pack(anchor="w")

    def _load(self):
        ex_dir = Path(self.var_ex_dir.get())
        try:
            self._exercises = load_exercises(ex_dir)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        if not self._exercises:
            messagebox.showerror("Error", f"No se encontraron ejercicios en:\n{ex_dir}")
            return

        total = sum(len(f) for asig in self._exercises.values() for f in asig.values())
        self._log(f"Cargados: {total} ejercicios")
        for asig in sorted(self._exercises):
            for tema, files in sorted(self._exercises[asig].items()):
                self._log(f"  {asig}/{tema}: {len(files)}")

        self._set_status(f"{total} ejercicios cargados", "#4caf50")
        self._update_temas()
        self.btn_gen.configure(state="normal")

    def _get_output_dir(self):
        today = date.today().strftime("%Y-%m-%d")
        return str(BASE_PATH / "examenes_generados" / today)

    def _get_active_temas(self, asig):
        active = []
        temas_map = CII_TEMAS if asig == "CII" else CCSS_TEMAS
        for tema_key in temas_map:
            key = f"{asig}_{tema_key}"
            if key in self._tema_vars and self._tema_vars[key].get():
                active.append(tema_key)
        return active

    def _start_gen(self):
        asig = self.var_asig.get()
        num = self.var_num.get()
        seed_str = self.var_seed.get().strip()
        seed = int(seed_str) if seed_str.isdigit() else None

        self.btn_gen.configure(state="disabled")
        self.btn_load.configure(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = num

        self._last_paths = []
        t = threading.Thread(
            target=self._gen_worker,
            args=(asig, num, seed),
            daemon=True)
        t.start()

    def _gen_worker(self, asig, num, seed):
        try:
            output_dir = self._get_output_dir()
            start_id = get_next_exam_id(output_dir)

            for i in range(num):
                exam_id = start_id + i
                s = (seed + i) if seed is not None else None

                if asig == "CII":
                    temas = self._get_active_temas("CII")
                    sections, labels = generate_cii_exam(self._exercises, temas, s)
                    tag = "CII"
                elif asig == "CCSS":
                    temas = self._get_active_temas("CCSS")
                    sections, labels = generate_ccss_exam(self._exercises, temas, s)
                    tag = "CCSS"
                else:
                    # Ambas: examen mezclado
                    temas_cii = self._get_active_temas("CII")
                    temas_ccss = self._get_active_temas("CCSS")
                    sections, labels = generate_mixed_both_exam(
                        self._exercises, temas_cii, temas_ccss, 6, s)
                    tag = "CII_y_CCSS"

                path = build_exam_pdf(sections, labels, exam_id, output_dir, tag, solved=False)
                self._last_paths.append(path)
                self.after(0, self._log, f"Examen {exam_id}: {Path(path).name}")
                self.after(0, self._update_progress, i + 1)

            self.after(0, self._gen_done, num)
        except Exception as e:
            self.after(0, self._gen_error, str(e))

    def _update_progress(self, val):
        self.progress["value"] = val

    def _gen_done(self, count):
        self._set_status(f"{count} examenes generados", "#4caf50")
        self._log(f"\n{count} examenes generados correctamente.")
        self.btn_gen.configure(state="normal")
        self.btn_load.configure(state="normal")
        self.btn_open.configure(state="normal")
        # Auto-open: single PDF or folder
        if len(self._last_paths) == 1 and Path(self._last_paths[0]).exists():
            os.startfile(self._last_paths[0])
        else:
            folder = Path(self._get_output_dir())
            if folder.exists():
                os.startfile(str(folder))

    def _gen_error(self, msg):
        self._set_status("Error", "#d32f2f")
        self._log(f"ERROR: {msg}")
        messagebox.showerror("Error", msg)
        self.btn_gen.configure(state="normal")
        self.btn_load.configure(state="normal")

    def _open_folder(self):
        folder = Path(self._get_output_dir())
        if folder.exists():
            os.startfile(str(folder))
        else:
            parent = folder.parent
            if parent.exists():
                os.startfile(str(parent))


if __name__ == "__main__":
    app = ExamApp()
    app.mainloop()
