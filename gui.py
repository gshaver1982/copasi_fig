# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:15:01 2026

@author: Garrett

copasi_figure.gui

Tkinter GUI for loading COPASI exports and exporting publication-quality plots.

This module depends on:
- parser.py
- plotting.py
- style.py

The GUI is intentionally simple:
1. open a COPASI export
2. inspect detected species
3. toggle measured/fitted traces
4. preview the figure
5. export to PDF/SVG/PNG
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .parser import CopasiColumnInfo, load_copasi_export
from .plotting import PlotOptions, plot_copasi_series
from .style import set_publication_style


class CopasiFigureGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("COPASI Figure Builder")
        self.geometry("1320x840")
        self.minsize(1120, 740)

        set_publication_style()

        self.df: Optional[pd.DataFrame] = None
        self.info: Optional[CopasiColumnInfo] = None
        self.current_path: Optional[Path] = None

        self.selected_species = tk.StringVar(value="")
        self.output_dir = tk.StringVar(value=str(Path.home()))
        self.figure_title = tk.StringVar(value="")
        self.xlabel = tk.StringVar(value="Time")
        self.ylabel = tk.StringVar(value="Value")
        self.theme = tk.StringVar(value="publication")
        self.figure_format = tk.StringVar(value="pdf")
        self.show_measured = tk.BooleanVar(value=True)
        self.show_fitted = tk.BooleanVar(value=True)
        self.normalize = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Open a COPASI export to begin.")

        self._build_ui()
        self._build_plot_canvas()
        self._draw_empty_plot()

    def _build_ui(self) -> None:
        outer = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        outer.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(outer, padding=10)
        right = ttk.Frame(outer, padding=10)
        outer.add(left, weight=1)
        outer.add(right, weight=4)

        file_box = ttk.LabelFrame(left, text="File", padding=10)
        file_box.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(file_box, text="Open COPASI export...", command=self.open_file).pack(fill=tk.X)
        ttk.Button(file_box, text="Choose output folder...", command=self.choose_output_dir).pack(
            fill=tk.X, pady=(8, 0)
        )
        ttk.Label(file_box, textvariable=self.output_dir, wraplength=330).pack(fill=tk.X, pady=(8, 0))

        controls = ttk.LabelFrame(left, text="Plot settings", padding=10)
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls, text="Theme").pack(anchor="w")
        self.theme_combo = ttk.Combobox(
            controls,
            state="readonly",
            values=["publication", "nature", "acs"],
            textvariable=self.theme,
        )
        self.theme_combo.pack(fill=tk.X, pady=(0, 8))
        self.theme_combo.bind("<<ComboboxSelected>>", lambda _: self.update_plot())

        ttk.Label(controls, text="Figure title").pack(anchor="w")
        ttk.Entry(controls, textvariable=self.figure_title).pack(fill=tk.X, pady=(0, 8))

        ttk.Label(controls, text="X label").pack(anchor="w")
        ttk.Entry(controls, textvariable=self.xlabel).pack(fill=tk.X, pady=(0, 8))

        ttk.Label(controls, text="Y label").pack(anchor="w")
        ttk.Entry(controls, textvariable=self.ylabel).pack(fill=tk.X, pady=(0, 8))

        ttk.Checkbutton(controls, text="Show measured values", variable=self.show_measured,
                        command=self.update_plot).pack(anchor="w")
        ttk.Checkbutton(controls, text="Show fitted values", variable=self.show_fitted,
                        command=self.update_plot).pack(anchor="w")
        ttk.Checkbutton(controls, text="Normalize each series", variable=self.normalize,
                        command=self.update_plot).pack(anchor="w")

        fmt_row = ttk.Frame(controls)
        fmt_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(fmt_row, text="Export format").pack(side=tk.LEFT)
        ttk.Combobox(
            fmt_row,
            state="readonly",
            values=["pdf", "svg", "png"],
            textvariable=self.figure_format,
            width=8,
        ).pack(side=tk.RIGHT)

        species_box = ttk.LabelFrame(left, text="Species", padding=10)
        species_box.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        ttk.Label(species_box, text="Select one or more species").pack(anchor="w")
        self.species_list = tk.Listbox(
            species_box,
            selectmode=tk.EXTENDED,
            exportselection=False,
            height=14,
        )
        self.species_list.pack(fill=tk.BOTH, expand=True, pady=(6, 6))
        self.species_list.bind("<<ListboxSelect>>", lambda _: self.update_plot())

        button_row = ttk.Frame(species_box)
        button_row.pack(fill=tk.X)
        ttk.Button(button_row, text="Select all", command=self.select_all_species).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4)
        )
        ttk.Button(button_row, text="Clear", command=self.clear_species_selection).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0)
        )

        export_box = ttk.LabelFrame(left, text="Export", padding=10)
        export_box.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(export_box, text="Save figure...", command=self.save_figure).pack(fill=tk.X)

        ttk.Label(left, textvariable=self.status, wraplength=340).pack(fill=tk.X)

        right_top = ttk.Panedwindow(right, orient=tk.VERTICAL)
        right_top.pack(fill=tk.BOTH, expand=True)

        table_frame = ttk.LabelFrame(right_top, text="Data preview", padding=8)
        plot_frame = ttk.LabelFrame(right_top, text="Figure preview", padding=8)
        right_top.add(table_frame, weight=1)
        right_top.add(plot_frame, weight=3)

        self.tree = ttk.Treeview(table_frame, show="headings", height=10)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        self.plot_frame = plot_frame

    def _build_plot_canvas(self) -> None:
        self.fig, self.ax = plt.subplots(figsize=(7.2, 5.0), constrained_layout=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

    def _draw_empty_plot(self) -> None:
        self.ax.clear()
        self.ax.text(
            0.5,
            0.5,
            "Open a COPASI export to preview the plot",
            ha="center",
            va="center",
            transform=self.ax.transAxes,
            fontsize=11,
        )
        self.ax.set_axis_off()
        self.canvas.draw_idle()

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open COPASI export",
            filetypes=[
                ("COPASI text exports", "*.txt *.tsv *.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            df, info = load_copasi_export(path)
        except Exception as exc:
            messagebox.showerror("Could not open file", str(exc))
            return

        self.df = df
        self.info = info
        self.current_path = Path(path)

        self.species_list.delete(0, tk.END)
        for sp in info.species:
            self.species_list.insert(tk.END, sp)
        self.species_list.selection_set(0, tk.END)

        if not self.figure_title.get():
            self.figure_title.set(self.current_path.stem)

        self.refresh_preview()
        self.update_plot()
        self.status.set(
            f"Loaded {self.current_path.name}: {len(df)} rows, {len(df.columns)} columns."
        )

    def choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose output folder", initialdir=self.output_dir.get())
        if path:
            self.output_dir.set(path)

    def select_all_species(self) -> None:
        self.species_list.selection_set(0, tk.END)
        self.update_plot()

    def clear_species_selection(self) -> None:
        self.species_list.selection_clear(0, tk.END)
        self.update_plot()

    def get_selected_species(self) -> list[str]:
        if self.info is None:
            return []
        indices = self.species_list.curselection()
        return [self.species_list.get(i) for i in indices]

    def refresh_preview(self) -> None:
        if self.df is None:
            return

        preview = self.df.head(50).copy()

        for col in self.tree["columns"]:
            self.tree.heading(col, text="")
        self.tree.delete(*self.tree.get_children())

        self.tree["columns"] = list(preview.columns)
        for col in preview.columns:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=130, anchor="center")

        for _, row in preview.iterrows():
            values = []
            for val in row.tolist():
                if pd.isna(val):
                    values.append("")
                else:
                    values.append(f"{val:.6g}" if isinstance(val, (float, int)) else str(val))
            self.tree.insert("", tk.END, values=values)

    def update_plot(self) -> None:
        if self.df is None or self.info is None:
            self._draw_empty_plot()
            return

        species = self.get_selected_species()
        if not species:
            self._draw_empty_plot()
            return

        options = PlotOptions(
            theme=self.theme.get().strip(),
            xlabel=self.xlabel.get().strip() or None,
            ylabel=self.ylabel.get().strip() or None,
            title=self.figure_title.get().strip() or None,
            show_measured=self.show_measured.get(),
            show_fitted=self.show_fitted.get(),
            normalize=self.normalize.get(),
        )

        try:
            fig, ax = plot_copasi_series(
                self.df,
                self.info,
                species=species,
                options=options,
                ax=self.ax,
            )
        except Exception as exc:
            messagebox.showerror("Plot failed", str(exc))
            return

        self.fig = fig
        self.ax = ax
        self.canvas.draw_idle()

    def save_figure(self) -> None:
        if self.df is None or self.info is None:
            messagebox.showwarning("Nothing to save", "Open a file and generate a plot first.")
            return

        ext = self.figure_format.get().strip().lower()
        if ext not in {"pdf", "svg", "png"}:
            messagebox.showerror("Invalid format", f"Unsupported format: {ext}")
            return

        initial_name = "copasi_figure." + ext
        outpath = filedialog.asksaveasfilename(
            title="Save figure",
            initialdir=self.output_dir.get(),
            initialfile=initial_name,
            defaultextension=f".{ext}",
            filetypes=[(f"{ext.upper()} file", f"*.{ext}"), ("All files", "*.*")],
        )
        if not outpath:
            return

        self.update_plot()

        try:
            self.fig.savefig(outpath, bbox_inches="tight")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        self.status.set(f"Saved figure to {outpath}")
        messagebox.showinfo("Saved", f"Figure saved to:\n{outpath}")


def main() -> None:
    app = CopasiFigureGUI()
    app.mainloop()


if __name__ == "__main__":
    main()