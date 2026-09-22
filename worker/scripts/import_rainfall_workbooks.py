"""Import RESA rainfall decade totals from legacy XLS workbooks.

The source sheets contain one observed cumulative value per station and decade,
not daily measurements. Values are stored in the dedicated decade-total table,
so the UI cannot mistake a decade total for a measurement on day 10, 20 or 31.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import xlrd

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.agro.registry import canonical_stations


MONTHS = {"AOUT": 8, "AOÛT": 8, "SEPT": 9, "SEPTEMBRE": 9}
SOURCE_FILES = {
    "RESA-01 AOUT 2026.xls": (2026, 8, 1),
    "RESA-02 AOUT 2026.xls": (2026, 8, 2),
    "RESA-03 AOUT 2026.xls": (2026, 8, 3),
    "RESA-01 SEPT 2026.xls": (2026, 9, 1),
}


def _key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def _last_day(month: int, decade: int) -> int:
    if decade == 1:
        return 10
    if decade == 2:
        return 20
    return 31


def read_totals(path: Path) -> dict[str, float]:
    sheet = xlrd.open_workbook(str(path), formatting_info=False).sheet_by_name("Feuil1, 2, 3")
    known = {_key(station.name): station.id for station in canonical_stations()}
    totals: dict[str, float] = {}
    for row in range(10, sheet.nrows):
        name = str(sheet.cell_value(row, 0)).strip()
        station = known.get(_key(name))
        value = sheet.cell_value(row, 4)
        if not station or not isinstance(value, (int, float)):
            continue
        totals[station] = round(float(value), 3)
    return totals


def import_file(path: Path, year: int, month: int, decade: int, dry_run: bool = False) -> dict[str, object]:
    totals = read_totals(path)
    payloads = [
        {
            "year": year,
            "month": month,
            "decade": decade,
            "station_id": station,
            "hauteur_mm": value,
        }
        for station, value in totals.items()
    ]
    if not dry_run:
        from app import db

        db.upsert_agro_rain_decades(payloads)
    return {"file": path.name, "year": year, "month": month, "decade": decade, "stations": len(payloads), "totals": totals}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path, help="Write the normalized payload JSON")
    args = parser.parse_args()
    if not args.dry_run:
        try:
            from app import db  # noqa: F401
        except ModuleNotFoundError as error:
            if error.name == "supabase":
                raise SystemExit(
                    "Dépendance manquante: supabase. Exécutez d'abord "
                    "python -m pip install -r requirements.txt"
                ) from error
            raise
    results = []
    for filename, period in SOURCE_FILES.items():
        path = args.directory / filename
        if not path.exists() and filename == "RESA-01 AOUT 2026.xls":
            path = args.directory.parent / filename
        if not path.exists():
            raise SystemExit(f"Fichier introuvable: {path}")
        results.append(import_file(path, *period, dry_run=args.dry_run))
    rendered = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
