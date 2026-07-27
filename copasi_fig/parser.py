# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 12:52:57 2026

@author: Garrett

copasi_fig.parser

Parse COPASI text exports into a normalized structure suitable for plotting.

This module is intentionally narrow:
- read tab/comma/semicolon separated COPASI export tables
- detect the independent variable column
- detect species names and measured/fitted columns
- provide a small metadata object the GUI and plotting code can use

Expected COPASI-style headers
-----------------------------
[Species].Measured Value
[Species].Fitted Value
[Species].Independent Value

The parser is permissive about whitespace and delimiter choice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

__all__ = [
    "CopasiColumnInfo",
    "read_copasi_table",
    "detect_copasi_columns",
    "load_copasi_export",
]

_SPECIES_PATTERN = re.compile(
    r"^\[(?P<species>.+?)\]\.(?P<kind>Measured|Fitted) Value$"
)
_INDEPENDENT_PATTERN = re.compile(r"Independent Value$")


@dataclass(frozen=True)
class CopasiColumnInfo:
    """Metadata describing a COPASI export table."""

    time_column: str
    species: List[str]
    measured_columns: Dict[str, str]
    fitted_columns: Dict[str, str]

    def has_species(self, species: str) -> bool:
        return species in self.species

    def species_columns(self, species: str) -> Tuple[str | None, str | None]:
        """Return (measured_column, fitted_column) for a species."""
        return self.measured_columns.get(species), self.fitted_columns.get(species)


def read_copasi_table(path: str | Path) -> pd.DataFrame:
    """Read a COPASI export table into a DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    try:
        df = pd.read_csv(path, sep=None, engine="python")
    except Exception as exc:
        raise ValueError(f"Could not parse COPASI table: {path}") from exc

    if df.empty:
        raise ValueError(f"The file is empty: {path}")

    return df


def detect_copasi_columns(df: pd.DataFrame) -> CopasiColumnInfo:
    """Detect COPASI column roles from a parsed table."""
    if df.empty:
        raise ValueError("Cannot detect columns in an empty table.")

    time_candidates = [c for c in df.columns if _INDEPENDENT_PATTERN.search(str(c))]
    if not time_candidates:
        raise ValueError(
            "Could not find an independent-value column. "
            "Expected a header containing 'Independent Value'."
        )
    time_column = time_candidates[0]

    species: List[str] = []
    measured_columns: Dict[str, str] = {}
    fitted_columns: Dict[str, str] = {}

    for col in df.columns:
        match = _SPECIES_PATTERN.match(str(col))
        if not match:
            continue

        sp = match.group("species")
        kind = match.group("kind")

        if sp not in species:
            species.append(sp)

        if kind == "Measured":
            measured_columns[sp] = col
        else:
            fitted_columns[sp] = col

    if not species:
        raise ValueError(
            "No COPASI species columns found. Expected headers like "
            "'[A].Measured Value' or '[A].Fitted Value'."
        )

    return CopasiColumnInfo(
        time_column=time_column,
        species=species,
        measured_columns=measured_columns,
        fitted_columns=fitted_columns,
    )


def load_copasi_export(path: str | Path) -> tuple[pd.DataFrame, CopasiColumnInfo]:
    """Convenience wrapper that reads a file and detects COPASI columns."""
    df = read_copasi_table(path)
    info = detect_copasi_columns(df)
    return df, info