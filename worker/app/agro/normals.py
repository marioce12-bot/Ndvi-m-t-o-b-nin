"""Climate normal lookup for the national agrometeorological stations."""

from __future__ import annotations

import json
from pathlib import Path

_path = Path(__file__).parents[1] / "data" / "climate_normals.json"
try:
    _NORMALS: dict[str, dict[str, dict[str, float]]] = json.loads(_path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError):
    _NORMALS = {}

_MONTH_KEYS = {1: "jan", 2: "fev", 3: "mar", 4: "avr", 5: "mai", 6: "jun", 7: "jul", 8: "aou", 9: "sep", 10: "oct", 11: "nov", 12: "dec"}


def _normal_decade_key(month: int, decade: int) -> str:
    return f"{_MONTH_KEYS.get(month, '')}{decade}"


def get_climate_normal(station_id: str, year: int, month: int, decade: int) -> dict[str, float] | None:
    del year
    station = _NORMALS.get(station_id) or _NORMALS.get(station_id.casefold())
    if not station:
        return None
    return station.get(_normal_decade_key(month, decade))
