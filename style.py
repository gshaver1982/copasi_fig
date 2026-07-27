# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:13:06 2026

@author: Garrett

copasi_figure.style

Matplotlib styling helpers for publication-quality COPASI figures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import matplotlib as mpl
from cycler import cycler

__all__ = [
    "FigureStyle",
    "set_publication_style",
    "apply_theme",
    "palette_for_series",
]


@dataclass(frozen=True)
class FigureStyle:
    """Container for common figure styling defaults."""

    font_family: str = "DejaVu Sans"
    font_size: int = 10
    line_width: float = 1.8
    marker_size: float = 4.5
    dpi: int = 150
    save_dpi: int = 600
    use_grid: bool = False


def set_publication_style(style: FigureStyle | None = None) -> None:
    """Set global matplotlib defaults for journal-style figures."""
    style = style or FigureStyle()

    mpl.rcParams.update(
        {
            "font.family": style.font_family,
            "font.size": style.font_size,
            "axes.labelsize": style.font_size,
            "axes.titlesize": style.font_size + 1,
            "xtick.labelsize": style.font_size - 1,
            "ytick.labelsize": style.font_size - 1,
            "legend.fontsize": style.font_size - 1,
            "axes.linewidth": 0.8,
            "lines.linewidth": style.line_width,
            "lines.markersize": style.marker_size,
            "figure.dpi": style.dpi,
            "savefig.dpi": style.save_dpi,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.grid": style.use_grid,
            "axes.prop_cycle": cycler(
                color=[
                    "#1f77b4",
                    "#ff7f0e",
                    "#2ca02c",
                    "#d62728",
                    "#9467bd",
                    "#8c564b",
                    "#e377c2",
                    "#7f7f7f",
                    "#bcbd22",
                    "#17becf",
                ]
            ),
        }
    )


def apply_theme(theme: str = "publication") -> None:
    """Apply a named styling preset."""
    theme = theme.lower().strip()

    if theme in {"publication", "journal", "default"}:
        set_publication_style(FigureStyle())
        return

    if theme == "nature":
        set_publication_style(
            FigureStyle(
                font_family="DejaVu Sans",
                font_size=10,
                line_width=1.8,
                marker_size=4.2,
                dpi=150,
                save_dpi=600,
            )
        )
        return

    if theme == "acs":
        set_publication_style(
            FigureStyle(
                font_family="DejaVu Sans",
                font_size=9,
                line_width=1.6,
                marker_size=4.0,
                dpi=150,
                save_dpi=600,
            )
        )
        return

    raise ValueError(f"Unknown theme: {theme}")


def palette_for_series(n: int) -> Sequence[str]:
    """Return a colorblind-safe palette sized for n series."""
    base = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    if n <= len(base):
        return base[:n]

    out: list[str] = []
    while len(out) < n:
        out.extend(base)
    return out[:n]