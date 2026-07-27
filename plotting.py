# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:13:57 2026

@author: Garrett


Plot COPASI exports in a publication-quality style.

This module stays independent from the GUI:
- it accepts a DataFrame plus parsed metadata
- it renders a single matplotlib Figure/Axes pair
- it can be used from scripts, notebooks, or the GUI

Typical usage
-------------
from copasi_figure.parser import load_copasi_export
from copasi_figure.plotting import plot_copasi_figure

df, info = load_copasi_export("example.txt")
fig, ax = plot_copasi_figure(
    df,
    info,
    species=["A", "B", "C"],
    show_measured=True,
    show_fitted=True,
)
fig.savefig("figure.pdf", bbox_inches="tight")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import pandas as pd

from .parser import CopasiColumnInfo
from .style import apply_theme, palette_for_series, set_publication_style

__all__ = [
    "PlotOptions",
    "plot_copasi_figure",
    "plot_copasi_series",
]


@dataclass(frozen=True)
class PlotOptions:
    """Configuration options for a COPASI plot."""

    theme: str = "publication"
    figsize: tuple[float, float] = (7.0, 4.8)
    xlabel: str | None = None
    ylabel: str | None = None
    title: str | None = None
    show_measured: bool = True
    show_fitted: bool = True
    normalize: bool = False
    legend: bool = True
    legend_frame: bool = False
    legend_ncols: int = 1
    tight_layout: bool = True
    remove_top_right_spines: bool = True
    measured_marker: str = "o"
    measured_linestyle: str = "None"
    fitted_marker: str | None = None
    fitted_linestyle: str = "-"
    measured_alpha: float = 1.0
    fitted_alpha: float = 1.0


def _clean_axes(ax: plt.Axes, remove_top_right_spines: bool = True) -> None:
    """Apply a simple journal-style axis appearance."""
    if remove_top_right_spines:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=4, width=0.8)
    ax.grid(False)


def _to_numeric_series(series: pd.Series) -> pd.Series:
    """Convert a column to numeric, coercing invalid entries to NaN."""
    return pd.to_numeric(series, errors="coerce")


def _normalize_series(series: pd.Series) -> pd.Series:
    """Normalize a numeric series to the range 0..1 when possible."""
    s = series.dropna()
    if s.empty:
        return series
    lo = s.min()
    hi = s.max()
    if hi == lo:
        return series * 0.0
    return (series - lo) / (hi - lo)


def _selected_species(
    info: CopasiColumnInfo,
    species: Sequence[str] | None,
) -> list[str]:
    """Resolve the species list, preserving the metadata order."""
    if species is None:
        return list(info.species)

    wanted = set(species)
    return [sp for sp in info.species if sp in wanted]


def plot_copasi_series(
    df: pd.DataFrame,
    info: CopasiColumnInfo,
    species: Sequence[str] | None = None,
    *,
    options: PlotOptions | None = None,
    ax: plt.Axes | None = None,
):
    """Plot one or more COPASI species on a single axes.

    Parameters
    ----------
    df:
        Parsed COPASI table.
    info:
        Column metadata returned by the parser.
    species:
        Species names to plot. If omitted, all detected species are used.
    options:
        Plot configuration.
    ax:
        Optional matplotlib Axes to draw on.

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
    """
    options = options or PlotOptions()
    apply_theme(options.theme)

    species_list = _selected_species(info, species)
    if not species_list:
        raise ValueError("No species selected for plotting.")

    if info.time_column not in df.columns:
        raise KeyError(f"Time column not found: {info.time_column}")

    if ax is None:
        fig, ax = plt.subplots(figsize=options.figsize, constrained_layout=options.tight_layout)
    else:
        fig = ax.figure

    _clean_axes(ax, options.remove_top_right_spines)

    x = _to_numeric_series(df[info.time_column])
    palette = palette_for_series(max(1, len(species_list) * 2))

    color_index = 0
    plotted_any = False

    for sp in species_list:
        measured_col = info.measured_columns.get(sp)
        fitted_col = info.fitted_columns.get(sp)

        if options.show_measured and measured_col and measured_col in df.columns:
            y = _to_numeric_series(df[measured_col])
            mask = x.notna() & y.notna()
            if mask.any():
                yy = y[mask]
                if options.normalize:
                    yy = _normalize_series(yy)
                ax.plot(
                    x[mask],
                    yy,
                    linestyle=options.measured_linestyle,
                    marker=options.measured_marker,
                    color=palette[color_index % len(palette)],
                    alpha=options.measured_alpha,
                    label=f"{sp} measured",
                )
                plotted_any = True
                color_index += 1

        if options.show_fitted and fitted_col and fitted_col in df.columns:
            y = _to_numeric_series(df[fitted_col])
            mask = x.notna() & y.notna()
            if mask.any():
                yy = y[mask]
                if options.normalize:
                    yy = _normalize_series(yy)
                ax.plot(
                    x[mask],
                    yy,
                    linestyle=options.fitted_linestyle,
                    marker=options.fitted_marker,
                    color=palette[color_index % len(palette)],
                    alpha=options.fitted_alpha,
                    label=f"{sp} fitted",
                )
                plotted_any = True
                color_index += 1

    if not plotted_any:
        ax.text(
            0.5,
            0.5,
            "No plottable series selected",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        ax.set_axis_off()
        return fig, ax

    ax.set_xlabel(options.xlabel or info.time_column)
    ax.set_ylabel(options.ylabel or ("Normalized value" if options.normalize else "Value"))
    if options.title:
        ax.set_title(options.title)

    if options.legend:
        ax.legend(frameon=options.legend_frame, ncols=options.legend_ncols)

    return fig, ax


def plot_copasi_figure(
    df: pd.DataFrame,
    info: CopasiColumnInfo,
    species: Sequence[str] | None = None,
    *,
    show_measured: bool = True,
    show_fitted: bool = True,
    normalize: bool = False,
    theme: str = "publication",
    figsize: tuple[float, float] = (7.0, 4.8),
    xlabel: str | None = None,
    ylabel: str | None = None,
    title: str | None = None,
):
    """Convenience wrapper for the most common plotting workflow."""
    options = PlotOptions(
        theme=theme,
        figsize=figsize,
        xlabel=xlabel,
        ylabel=ylabel,
        title=title,
        show_measured=show_measured,
        show_fitted=show_fitted,
        normalize=normalize,
    )
    return plot_copasi_series(
        df=df,
        info=info,
        species=species,
        options=options,
    )
```
