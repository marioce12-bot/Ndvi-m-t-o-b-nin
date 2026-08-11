"""Pentadal calendar and USGS index listing."""

from __future__ import annotations

import re
import time
from datetime import date, timedelta

import requests

from .products import PRODUCTS

MONTHS = (
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
)
_CACHE: dict[str, tuple[float, list[dict[str, object]]]] = {}
CACHE_TTL_SECONDS = 3600


def _validate_number(num: int) -> None:
    if not 1 <= num <= 72:
        raise ValueError("Le numero de pentade doit etre compris entre 1 et 72")


def pentade_to_dates(year: int, num: int) -> tuple[date, date]:
    """Return the inclusive start and end dates for a pentade."""
    _validate_number(num)
    month = (num - 1) // 6 + 1
    slot = (num - 1) % 6
    start_day = slot * 5 + 1
    start = date(year, month, start_day)
    if slot == 5:
        end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    else:
        end = start + timedelta(days=4)
    return start, end


def pentade_label(year: int, num: int) -> str:
    start, end = pentade_to_dates(year, num)
    if start.month == end.month:
        days = f"{start.day}-{end.day}"
        return f"{days} {MONTHS[start.month - 1]} {year}"
    return f"{start.day}-{end.day} {MONTHS[start.month - 1]}-{MONTHS[end.month - 1]} {year}"


def list_available(product: str) -> list[dict[str, object]]:
    """List pentades published in the selected USGS directory."""
    if product not in PRODUCTS:
        raise ValueError(f"Produit inconnu: {product}")
    now = time.monotonic()
    cached = _CACHE.get(product)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    config = PRODUCTS[product]
    response = requests.get(config["directory"], timeout=30)
    response.raise_for_status()
    pattern = re.compile(config["pattern"])
    pentades: list[dict[str, object]] = []
    for match in pattern.finditer(response.text):
        year = 2000 + int(match.group("yy"))
        num = int(match.group("pp"))
        if not 1 <= num <= 72:
            continue
        pentades.append(
            {
                "id": f"{year}-P{num:02d}",
                "label": pentade_label(year, num),
                "year": year,
                "num": num,
                "url": f"{config['directory']}{match.group(0)}",
            }
        )
    pentades.sort(key=lambda item: (item["year"], item["num"]), reverse=True)
    _CACHE[product] = (now, pentades)
    return pentades
