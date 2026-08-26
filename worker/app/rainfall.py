"""Rainfall workbook ingestion and RESA-01 calculations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import xlrd


@dataclass(frozen=True)
class RainfallImport:
    year: int
    month: int
    decade: int
    source: str
    rows: list[dict[str, Any]]


MONTHS = {"JANVIER": 1, "FEVRIER": 2, "FÉVRIER": 2, "MARS": 3, "AVRIL": 4, "MAI": 5, "JUIN": 6, "JUILLET": 7, "AOUT": 8, "AOÛT": 8, "SEPTEMBRE": 9, "OCTOBRE": 10, "NOVEMBRE": 11, "DECEMBRE": 12, "DÉCEMBRE": 12}


def _number(value: object) -> float | None:
    if value in (None, "", '"'):
        return None
    if isinstance(value, str) and value.strip().upper() in {"T", "TR"}:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _metadata(sheet: Any) -> tuple[int, int, int]:
    values = [str(sheet.cell_value(r, c)).strip() for r in range(min(sheet.nrows, 12)) for c in range(sheet.ncols)]
    year = next((int(float(v)) for v in values if re.fullmatch(r"20\d{2}(?:\.0)?", v)), 0)
    month_name = next((v.upper() for v in values if v.upper() in MONTHS), "")
    decade_map = {"I": 1, "II": 2, "III": 3}
    decade = next((decade_map[v.upper()] for v in values if v.upper() in decade_map), 0)
    if not year or not month_name or not decade:
        raise ValueError("Métadonnées année/mois/décade introuvables")
    return year, MONTHS[month_name], decade


def parse_decades_xls(content: bytes) -> RainfallImport:
    book = xlrd.open_workbook(file_contents=content)
    sheet = next((s for s in book.sheets() if s.nrows and any("HAUTEURS JOURNALIERES" in str(s.cell_value(r, c)).upper() for r in range(min(s.nrows, 10)) for c in range(s.ncols))), None)
    if sheet is None:
        raise ValueError("Feuille DECADES introuvable")
    # DECADES files contain repeated department blocks. Header rows identify
    # the daily columns; data rows are normalized without trusting summaries.
    year, month, decade = _metadata(sheet)
    rows: list[dict[str, Any]] = []
    department = ""
    for r in range(sheet.nrows):
        values = [sheet.cell_value(r, c) for c in range(sheet.ncols)]
        text = " ".join(str(v).strip() for v in values[:3] if v not in ("", None)).strip()
        if text.upper() in {"ATLANTIQUE-LITTORAL", "ATACORA-DONGA", "BORGOU-ALIBORI", "MONO-COUFFO", "OUEME-PLATEAU", "ZOU-COLLINE"}:
            department = text
            continue
        localite = str(values[1]).strip() if len(values) > 1 and values[1] not in ("", None) else ""
        if not department or not localite or localite.upper() in {"LOCALITES", "DEPARTEMENTS"}:
            continue
        daily = [_number(values[c]) for c in range(2, min(13, len(values)))]
        if any(value is not None for value in daily):
            rows.append({"department": department, "station": localite, "daily": daily})
    return RainfallImport(year, month, decade, "decades", rows)


def compute_resa_row(row: dict[str, Any], normal_cuma: float | None = None, etp: float | None = None) -> dict[str, Any]:
    daily = [value for value in row.get("daily", []) if value is not None]
    total = sum(daily)
    return {**row, "nbRainDays": sum(value >= 1 for value in daily), "nbOver20": sum(value > 20 for value in daily), "maxDaily": max(daily, default=None), "decadeTotal": total, "decadeDeviation": total - normal_cuma if normal_cuma is not None else None, "waterBalance": total - etp if etp is not None else None}
