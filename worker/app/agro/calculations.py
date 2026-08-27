"""Pure calculations for the agrometeorological bulletin."""

from __future__ import annotations

from datetime import date, datetime
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


TABLEAU_BLOCKS = (
    ("Tableau 1", ("Alibori", "Atacora", "Borgou", "Donga")),
    ("Tableau 2", ("Collines", "Couffo", "Mono", "Zou")),
    ("Tableau 3", ("Atlantique", "Littoral", "Oueme", "Plateau")),
)
VALID_DEPARTMENTS = {department.upper() for _, departments in TABLEAU_BLOCKS for department in departments}


def season_start(station: Station, observed_on: date) -> date | None:
    department = station.department.upper()
    if any(name in department for name in ("ATACORA", "DONGA", "BORGOU", "ALIBORI")):
        return date(observed_on.year, 4, 1) if 4 <= observed_on.month <= 10 else None
    if 3 <= observed_on.month <= 7:
        return date(observed_on.year, 3, 1)
    if 9 <= observed_on.month <= 11:
        return date(observed_on.year, 9, 1)
    return None


def rolling_totals(station: Station, current_end: date, history: Iterable[DailyRain]) -> tuple[float, float | None]:
    values = [item for item in history if item.station_id == station.id and item.observed_on <= current_end and item.amount_mm is not None]
    year_total = sum(item.amount_mm for item in values if item.observed_on.year == current_end.year)
    start = season_start(station, current_end)
    season_total = sum(item.amount_mm for item in values if start and start <= item.observed_on <= current_end) if start else None
    return year_total, season_total


def grouped_stations(stations: Iterable[Station]) -> list[tuple[str, str, list[Station]]]:
    by_department = {station.department.upper(): [] for station in stations}
    for station in stations:
        if station.department.upper() not in VALID_DEPARTMENTS:
            raise ValueError(f"Département hors référentiel RESA: {station.department}")
        by_department[station.department.upper()].append(station)
    result: list[tuple[str, str, list[Station]]] = []
    for block, departments in TABLEAU_BLOCKS:
        for department in departments:
            result.append((block, department, by_department.get(department.upper(), [])))
    return result


def resolve_etp_station(station: Station, stations: dict[str, Station]) -> Station | None:
    if station.principal:
        return station
    return stations.get(station.etp_station_id) if station.etp_station_id else None


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
    current_end = max((item.observed_on for item in current), default=date(year, month, 1))
    year_total, season_total = rolling_totals(station, current_end, list(history_rain) + current)
    agro = list(agro_days)
    sunshine_total = sum(item.sunshine or 0 for item in agro)
    h10 = astronomical.h10 if astronomical else None
    fraction = sunshine_total / h10 * 100 if h10 else None
    radiation = astronomical.ra * (astronomical.angstrom_a + astronomical.angstrom_b * sunshine_total / h10) if astronomical and astronomical.ra is not None and h10 else None
    etp = editable.etp if editable else None
    return DecadeSummary(station.id, year, month, decade, rain_days, heavy_days, total, maximum, rainfall_normal.decade_total if rainfall_normal else None, year_total, year_total - rainfall_normal.annual_total if rainfall_normal and rainfall_normal.annual_total is not None else None, season_total, rainfall_normal.season_total if rainfall_normal else None, season_total - rainfall_normal.season_total if rainfall_normal and rainfall_normal.season_total is not None else None, (total - etp) if total is not None and etp is not None else None, h10, fraction, radiation, editable.ew if editable else None, etp)
