"""Import station rainfall normals from the RESA Excel workbook."""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

import xlrd


DECADE_PREFIXES = {
    "j": "ja",
    "f": "fe",
    "m": "mr",
    "a": "av",
    "ma": "mi",
    "ju": "jn",
    "s": "se",
    "o": "oc",
    "n": "no",
    "d": "de",
}


def normalize_key(value: object) -> str:
    text = "".join(
        char for char in unicodedata.normalize("NFKD", str(value)) if not unicodedata.combining(char)
    )
    return text.casefold().strip().replace("_", "-").replace(" ", "-")


def import_normals(source: Path) -> dict[str, dict[str, dict[str, float | None]]]:
    sheet = xlrd.open_workbook(str(source), formatting_info=False).sheet_by_name("Normales")
    result: dict[str, dict[str, dict[str, float | None]]] = {}
    for column in range(sheet.ncols - 2):
        name = str(sheet.cell_value(1, column)).strip()
        if not name:
            continue
        if str(sheet.cell_value(1, column + 1)).strip().upper() != "CUMA":
            continue
        if str(sheet.cell_value(1, column + 2)).strip().upper() != "CUMS":
            continue
        station: dict[str, dict[str, float | None]] = {}
        for row in range(2, 38):
            label = str(sheet.cell_value(row, 0)).strip()
            if not label:
                continue
            # The worksheet reuses j/a/m labels for successive months. The
            # first 36 rainfall rows are ordered Jan-Dec and distinguish the
            # duplicate labels by position.
            month_prefix = ("ja", "fe", "mr", "av", "mi", "jn", "jl", "ao", "se", "oc", "no", "de")[(row - 2) // 3]
            decade = (row - 2) % 3 + 1
            station[f"{month_prefix}{decade}"] = {
                "annual": sheet.cell_value(row, column + 1) or None,
                "decade": sheet.cell_value(row, column) or None,
                "season": sheet.cell_value(row, column + 2) or None,
            }
        result[normalize_key(name)] = station
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parents[1] / "data" / "rainfall_normals.json")
    args = parser.parse_args()
    data = import_normals(args.source)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(data)} stations into {args.output}")


if __name__ == "__main__":
    main()
