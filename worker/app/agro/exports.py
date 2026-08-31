"""Independent Excel exports for the agrometeorological bulletin."""

from __future__ import annotations

from io import BytesIO
from typing import Iterable

import openpyxl
from openpyxl.styles import Font, PatternFill

from .calculations import grouped_stations, resolve_etp_station
from .models import DailyAgro, DailyRain, EditableDecadeValues, RainfallNormal, Station

MONTHS = ("JANVIER", "FEVRIER", "MARS", "AVRIL", "MAI", "JUIN", "JUILLET", "AOUT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DECEMBRE")
NETWORK_HEADERS = ["STATIONS", "Nbre jours pluie > 00mm", "Nbre jours pluie > 20mm", "Sur la décade en cours", "Ecart à la normale", "Depuis début année civile", "Ecart à la normale", "Depuis début Saison des pluies", "Ecart à la normale"]


def _download(workbook: openpyxl.Workbook, filename: str) -> tuple[BytesIO, str]:
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream, filename


def build_network_export(year: int, month: int, decade: int, stations: Iterable[Station], summaries: dict[str, object]) -> tuple[BytesIO, str]:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Réseau pluviométrique"
    sheet.append(["ANNEE", year, "MOIS", MONTHS[month - 1], "DECADE", decade])
    sheet.append(["V-b - DONNEES PLUVIOMETRIQUES"])
    sheet.append(["REPARTITION", "", "CUMUL OBSERVE (mm et /10)"])
    station_map = {station.id: station for station in stations}
    grouped = grouped_stations(stations)
    block_departments = {}
    for block, department, _ in grouped:
        block_departments.setdefault(block, []).append(department)
    for block, department, members in grouped:
        if not members:
            continue
        sheet.append([block, f"DEPARTEMENTS : {', '.join(block_departments[block])}"])
        sheet.append([f"DEPARTEMENT : {department}"])
        sheet.append(NETWORK_HEADERS)
        for station in members:
            summary = summaries.get(station.id, {})
            sheet.append([station.name, summary.get("rain_days"), summary.get("heavy_rain_days"), summary.get("rainfall_total"), summary.get("decade_deviation"), summary.get("year_total"), summary.get("year_deviation"), summary.get("season_total"), summary.get("season_deviation")])
    for row in sheet.iter_rows():
        for cell in row:
            if cell.column == 6 and isinstance(cell.value, (int, float)): cell.number_format = "0.0%"
    sheet.append([])
    sheet.append(["Notes : Nord : saison du 1er avril au 31 octobre. Sud : du 1er mars au 31 juillet puis du 1er septembre au 30 novembre."])
    sheet.append(["- : donnée manquante. Bilan hydrique = pluie de la décade - ETP de rattachement."])
    for cell in sheet[2]: cell.font = Font(bold=True, size=14)
    for row in sheet.iter_rows():
        if row and row[0].value in NETWORK_HEADERS: 
            for cell in row: cell.font = Font(bold=True); cell.fill = PatternFill("solid", fgColor="D9EAD3")
    return _download(workbook, f"RESA-{decade}_{MONTHS[month - 1]}_{year}.xlsx")


def build_climate_export(year: int, month: int, decade: int, stations: Iterable[Station], climate: dict[str, dict[str, object]]) -> tuple[BytesIO, str]:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Données climatiques"
    sheet.append(["ANNEE", year, "MOIS", MONTHS[month - 1], "DECADE", decade])
    sheet.append(["TABLEAU IV - DONNEES CLIMATIQUES (Moyennes sur décade)"])
    sheet.append(["STATIONS", "Fract. Insol (%)", "Ray. Global (j/cm²)", "ew", "ETP", "H×10", "Tmin", "Tmax", "Tmoy", "Sol +10", "Sol +50", "Hum min", "Hum max", "Hum moy", "Vapeur", "Déficit"])
    for station in stations:
        values = climate.get(station.id, {})
        sheet.append([station.name] + [values.get(key) for key in ("insolation_fraction", "global_radiation", "ew", "etp", "h10", "tmin", "tmax", "tmean", "soil10", "soil50", "humidity_min", "humidity_max", "humidity_mean", "vapor_pressure", "deficit")])
        sheet.append(["Ecart/Normale"] + [values.get(f"{key}_deviation") for key in ("tmin", "tmax", "tmean", "humidity_min", "humidity_max", "humidity_mean")])
    sheet.append([])
    sheet.append(["TABLEAU V-a - DONNEES CLIMATIQUES COMPLEMENTAIRES"])
    sheet.append(["STATIONS", "Durée Insolation h/10", "Fraction Insolation %", "Rayonnement Global", "Vent moyen", "Vent maxi", "EVAPO. Bac", "ETP Penman", "Bilan hydrique potentiel"])
    for station in stations:
        values = climate.get(station.id, {})
        sheet.append([station.name] + [values.get(key) for key in ("sunshine_total", "insolation_fraction", "global_radiation", "wind_mean", "wind_max", "pan_evaporation", "etp", "water_balance")])
    sheet.append([])
    sheet.append(["* L'humidité moyenne (Umoy) est calculée à partir de la température moyenne."])
    sheet.append(["* Déficit de saturation = ew - tension de vapeur moyenne."])
    sheet.append(["* Les données manquantes sont codées par -."])
    for row in (sheet[2],):
        for cell in row: cell.font = Font(bold=True); cell.fill = PatternFill("solid", fgColor="D9EAD3")
    return _download(workbook, f"DONNEES_CLIMATIQUES-{decade}_{MONTHS[month - 1]}_{year}.xlsx")
