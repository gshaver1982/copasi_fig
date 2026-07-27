# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:17:11 2026

@author: Garrett

copasi_fig

Small toolkit for turning COPASI exports into publication-quality figures.
"""

from .parser import CopasiColumnInfo, detect_copasi_columns, load_copasi_export, read_copasi_table
from .plotting import PlotOptions, plot_copasi_figure, plot_copasi_series
from .style import FigureStyle, apply_theme, palette_for_series, set_publication_style

__all__ = [
    "CopasiColumnInfo",
    "detect_copasi_columns",
    "load_copasi_export",
    "read_copasi_table",
    "PlotOptions",
    "plot_copasi_figure",
    "plot_copasi_series",
    "FigureStyle",
    "apply_theme",
    "palette_for_series",
    "set_publication_style",
]