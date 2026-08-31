"""Independent Excel exports for the agrometeorological bulletin."""

from __future__ import annotations

from io import BytesIO
from typing import Iterable

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .calculations import grouped_stations, resolve_etp_station
from .models import DailyAgro, DailyRain, EditableDecadeValues, RainfallNormal, Station

MONTHS = ("JANVIER", "FEVRIER", "MARS", "AVRIL", "MAI", "JUIN", "JUILLET", "AOUT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DECEMBRE")
NETWORK_HEADERS = ["STATIONS", "LONGITUDE", "LATITUDE", "Nbre jours pluie > 00mm", "Nbre jours pluie > 20mm", "Sur la décade en cours", "Ecart à la normale", "% de la normale", "Depuis début année civile", "Ecart à la normale", "Depuis début Saison des pluies", "Ecart à la normale", "Bilan hydrique"]


def _download(workbook: openpyxl.Workbook, filename: str) -> tuple[BytesIO, str]:
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream, filename


def _style_table(sheet: openpyxl.worksheet.worksheet.Worksheet, header_row: int, widths: list[int]) -> None:
    border = Border(*(Side(style="thin", color="9BB7A2") for _ in range(4)))
    for row in sheet.iter_rows(min_row=header_row, max_row=sheet.max_row, min_col=1, max_col=len(widths)):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for cell in sheet[header_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="196B3A")
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[openpyxl.utils.get_column_letter(index)].width = width
    sheet.freeze_panes = None


def build_network_export(year: int, month: int, decade: int, stations: Iterable[Station], summaries: dict[str, object]) -> tuple[BytesIO, str]:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Réseau pluviométrique"
    groups = (("TABLEAU 1", ("Alibori", "Atacora", "Borgou", "Donga")), ("TABLEAU 2", ("Collines", "Couffo", "Mono", "Zou")), ("TABLEAU 3", ("Atlantique", "Littoral", "Oueme", "Plateau")))
    stations = list(stations)
    for table_number, departments in groups:
        if sheet.max_row > 1:
            sheet.append([])
        start = sheet.max_row + 1
        sheet.merge_cells(start_row=start, start_column=1, end_row=start, end_column=12)
        sheet.cell(start, 1, f"ANNEE : {year} | MOIS : {MONTHS[month - 1]} | DECADE : {decade} | {table_number}")
        sheet.cell(start, 1).font = Font(bold=True, size=13, color="FFFFFF")
        sheet.cell(start, 1).fill = PatternFill("solid", fgColor="0D472B")
        sheet.cell(start, 1).alignment = Alignment(horizontal="center")
        sheet.merge_cells(start_row=start + 1, start_column=1, end_row=start + 1, end_column=12)
        sheet.cell(start + 1, 1, "RESEAU PLUVIOMETRIQUE - DEPARTEMENTS : " + ", ".join(departments))
        sheet.cell(start + 1, 1).font = Font(bold=True)
        sheet.append(NETWORK_HEADERS)
        header_row = sheet.max_row
        for department in departments:
            members = [station for station in stations if station.department == department]
            if not members:
                continue
            department_row = sheet.max_row + 1
            sheet.append([department])
            for cell in sheet[department_row][:12]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="4E8B5D")
            for station in members:
                summary = summaries.get(station.id, {})
                sheet.append([station.name, summary.get("longitude", station.longitude), summary.get("latitude", station.latitude), summary.get("rain_days"), summary.get("heavy_rain_days"), summary.get("rainfall_total"), summary.get("decade_deviation"), summary.get("normal_percentage"), summary.get("year_total"), summary.get("year_deviation"), summary.get("season_total"), summary.get("season_deviation"), summary.get("water_balance")])
        _style_table(sheet, header_row, [24, 13, 13, 14, 14, 18, 18, 18, 20, 18, 24, 18, 16])
    return _download(workbook, f"DONNEES_PLUVIOMETRIQUES_{year}_{month:02d}_D{decade}.xlsx")


def build_climate_export(year: int, month: int, decade: int, stations: Iterable[Station], climate: dict[str, dict[str, object]]) -> tuple[BytesIO, str]:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Données climatiques"
    sheet.merge_cells("A1:I1")
    sheet["A1"] = "V-a - DONNEES CLIMATIQUES COMPLEMENTAIRES"
    sheet["A1"].font = Font(bold=True, size=15, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor="0D472B")
    sheet["A1"].alignment = Alignment(horizontal="center")
    sheet.merge_cells("A2:I2")
    sheet["A2"] = f"Période : {decade}ère décade de {MONTHS[month - 1].title()} {year}"
    sheet["A2"].alignment = Alignment(horizontal="center")
    sheet.append([])
    sheet.append(["STATIONS", "Durée Insolation h./10", "Fraction Insolation %", "Rayonn. Global j/cm²", "Vent moyen", "Vent maxi.", "EVAPO. Bac", "ETP Penman", "Bilan hydrique potentiel"])
    for station in stations:
        values = climate.get(station.id, {})
        sheet.append([station.name] + [values.get(key) for key in ("sunshine_total", "insolation_fraction", "global_radiation", "wind_mean", "wind_max", "pan_evaporation", "etp", "water_balance")])
    _style_table(sheet, 4, [22, 22, 22, 24, 16, 16, 16, 16, 25])
    sheet.auto_filter.ref = f"A4:I{sheet.max_row}"
    return _download(workbook, f"DONNEES_CLIMATIQUES_{year}_{month:02d}_D{decade}.xlsx")
    
    sheet.append([])
    sheet.append(["* L'humidité moyenne (Umoy) est calculée à partir de la température moyenne."])
    sheet.append(["* Déficit de saturation = ew - tension de vapeur moyenne."])
    sheet.append(["* Les données manquantes sont codées par -."])
    for row in (sheet[2],):
        for cell in row: cell.font = Font(bold=True); cell.fill = PatternFill("solid", fgColor="D9EAD3")
    return _download(workbook, f"DONNEES_CLIMATIQUES-{decade}_{MONTHS[month - 1]}_{year}.xlsx")
