"""Extract station-specific rainfall normals from a RESA Normales sheet."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import xlrd

sys.path.insert(0, str(Path(__file__).parents[1]))
from app.agro.registry import canonical_stations


def key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]", "", text)


def extract(path: Path) -> dict[str, dict[str, dict[str, float | None]]]:
    sheet = xlrd.open_workbook(str(path)).sheet_by_name("Normales")
    stations = {key(s.name): s.id for s in canonical_stations()}
    result: dict[str, dict[str, dict[str, float | None]]] = {}
    for col in range(sheet.ncols - 2):
        name = str(sheet.cell_value(1, col)).strip()
        if key(name) not in stations:
            continue
        if str(sheet.cell_value(1, col + 1)).strip().upper() != "CUMA":
            continue
        station_id = stations[key(name)]
        values = result.setdefault(station_id, {})
        for row in range(2, sheet.nrows):
            code = str(sheet.cell_value(row, col - 5 if col >= 5 else 0)).strip().lower()
            if not re.fullmatch(r"[a-z]+[123]", code):
                continue
            def number(offset: int) -> float | None:
                value = sheet.cell_value(row, col + offset)
                return float(value) if isinstance(value, (int, float)) else None
            values[code] = {"decade": number(0), "annual": number(1), "season": number(2)}
    return result


if __name__ == "__main__":
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    output.write_text(json.dumps(extract(source), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
