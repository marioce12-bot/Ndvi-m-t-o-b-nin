"""Pure calculations for the agrometeorological bulletin."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from .models import AstronomicalConstant, DailyAgro, DailyRain, DecadeSummary, EditableDecadeValues, RainfallNormal, Station


def rain_statistics(values: Iterable[float | None]) -> tuple[int, int, float | None, float | None]:
    valid = [value for value in values if value is not None]
    if not valid:
        return 0, 0, None, None
    return sum(value > 0 for value in valid), sum(value > 20 for value in valid), max(valid), sum(valid)


def season_contains(station: Station, month: int) -> bool:
    department = station.department.upper()
    north = any(name in department for name in ("ATACORA", "DONGA", "BORGOU", "ALIBORI"))
    return 4 <= month <= 10 if north else 3 <= month <= 7 or 9 <= month <= 11


def build_summary(
    station: Station,
    year: int,
    month: int,
    decade: int,
    current_rain: Iterable[DailyRain],
    history_rain: Iterable[DailyRain],
    rainfall_normal: RainfallNormal | None = None,
    editable: EditableDecadeValues | None = None,
    astronomical: AstronomicalConstant | None = None,
    agro_days: Iterable[DailyAgro] = (),
) -> DecadeSummary:
    current = list(current_rain)
    rain_days, heavy_days, maximum, total = rain_statistics(item.amount_mm for item in current)
    history = [item for item in history_rain if item.observed_on.year == year and item.observed_on <= date(year, month, min(28, 1 + decade * 10))]
    year_total = sum(item.amount_mm or 0 for item in history) + (total or 0)
    season_total = sum(item.amount_mm or 0 for item in history if season_contains(station, item.observed_on.month)) + ((total or 0) if season_contains(station, month) else 0)
    agro = list(agro_days)
    sunshine_total = sum(item.sunshine or 0 for item in agro)
    h10 = astronomical.h10 if astronomical else None
    fraction = sunshine_total / h10 * 100 if h10 else None
    radiation = astronomical.ra * (astronomical.angstrom_a + astronomical.angstrom_b * sunshine_total / h10) if astronomical and astronomical.ra is not None and h10 else None
    etp = editable.etp if editable else None
    return DecadeSummary(station.id, year, month, decade, rain_days, heavy_days, total, maximum, rainfall_normal.decade_total if rainfall_normal else None, year_total, year_total - rainfall_normal.annual_total if rainfall_normal and rainfall_normal.annual_total is not None else None, season_total, rainfall_normal.season_total if rainfall_normal else None, season_total - rainfall_normal.season_total if rainfall_normal and rainfall_normal.season_total is not None else None, (total - etp) if total is not None and etp is not None else None, h10, fraction, radiation, editable.ew if editable else None, etp)
