"""Independent Excel exports for the agrometeorological bulletin."""

from __future__ import annotations

from io import BytesIO
from typing import Iterable

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .models import Station

MONTHS = ("JANVIER", "FEVRIER", "MARS", "AVRIL", "MAI", "JUIN", "JUILLET", "AOUT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DECEMBRE")
NETWORK_SUMMARY_HEADERS = ["STATIONS", "LONGITUDE", "LATITUDE", "Nbre jours pluie > 00mm", "Nbre jours pluie > 20mm", "Sur la décade en cours", "Ecart à la normale", "% de la normale", "Depuis début année civile", "Ecart à la normale", "Depuis début Saison des pluies", "Ecart à la normale", "Bilan hydrique"]
NETWORK_DAILY_HEADERS = [f"J{day}" for day in range(1, 11)]
NETWORK_HEADERS = NETWORK_SUMMARY_HEADERS + NETWORK_DAILY_HEADERS
NETWORK_SUMMARY_COLUMN_COUNT = len(NETWORK_SUMMARY_HEADERS)  # 13 -> dernière colonne du bloc résumé = "Bilan hydrique"
OBSERVATIONS_HEADERS = ["Jour", "Pluie", "Tmin", "Tmax", "T moy", "Temp. 10cm", "Temp. 50cm", "Vent moyen", "Vent maxi", "Insolation", "Hum. min", "Hum. max", "Hum. moy", "Tension vapeur", "Évapo. bac"]
OBSERVATIONS_VAPOR_PRESSURE_COLUMN = "N"  # colonne "Tension vapeur" dans OBSERVATIONS_HEADERS


def _download(workbook: openpyxl.Workbook, filename: str) -> tuple[BytesIO, str]:
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream, filename


def _title_row_height(font_size: int) -> float:
    """Hauteur de ligne suffisante pour un titre en gras de `font_size` pt.

    La hauteur de ligne par défaut d'openpyxl (~15pt) est calibrée pour du texte
    à 11pt : avec un titre en gras à 13-15pt elle est trop courte et le texte
    apparaît tassé/coupé (surtout sur les visionneuses mobiles). On force donc
    une hauteur proportionnelle au corps du texte.
    """
    return round(font_size * 1.7, 1)


def _style_table(sheet: openpyxl.worksheet.worksheet.Worksheet, header_row: int, widths: list[int], divider_col: int | None = None) -> None:
    border = Border(*(Side(style="thin", color="9BB7A2") for _ in range(4)))
    for row in sheet.iter_rows(min_row=header_row, max_row=sheet.max_row, min_col=1, max_col=len(widths)):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if divider_col:
        # Bordure plus marquée à droite de `divider_col` pour signaler visuellement
        # la fin du bloc résumé (ex: la colonne "Bilan hydrique"), avant les blocs
        # de détail qui continuent la table (ex: pluies journalières).
        thick = Side(style="medium", color="0D472B")
        for row in sheet.iter_rows(min_row=header_row, max_row=sheet.max_row, min_col=divider_col, max_col=divider_col):
            for cell in row:
                cell.border = Border(left=cell.border.left, top=cell.border.top, bottom=cell.border.bottom, right=thick)
    for cell in sheet[header_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="196B3A")
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[openpyxl.utils.get_column_letter(index)].width = width
    sheet.freeze_panes = None
    sheet.sheet_view.showGridLines = True
    sheet.sheet_view.zoomScale = 90


def build_network_export(year: int, month: int, decade: int, stations: Iterable[Station], summaries: dict[str, object]) -> tuple[BytesIO, str]:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Réseau pluviométrique"
    groups = (("TABLEAU 1", ("Alibori", "Atacora", "Borgou", "Donga")), ("TABLEAU 2", ("Collines", "Couffo", "Mono", "Zou")), ("TABLEAU 3", ("Atlantique", "Littoral", "Oueme", "Plateau")))
    stations = list(stations)
    total_columns = len(NETWORK_HEADERS)
    for table_number, departments in groups:
        if sheet.max_row > 1:
            sheet.append([])
        start = sheet.max_row + 1
        sheet.merge_cells(start_row=start, start_column=1, end_row=start, end_column=total_columns)
        sheet.cell(start, 1, f"ANNEE : {year} | MOIS : {MONTHS[month - 1]} | DECADE : {decade} | {table_number}")
        sheet.cell(start, 1).font = Font(bold=True, size=13, color="FFFFFF")
        sheet.cell(start, 1).fill = PatternFill("solid", fgColor="0D472B")
        sheet.cell(start, 1).alignment = Alignment(horizontal="center")
        sheet.row_dimensions[start].height = _title_row_height(13)
        sheet.merge_cells(start_row=start + 1, start_column=1, end_row=start + 1, end_column=total_columns)
        sheet.cell(start + 1, 1, "RESEAU PLUVIOMETRIQUE - DEPARTEMENTS : " + ", ".join(departments))
        sheet.cell(start + 1, 1).font = Font(bold=True)
        # Sous-titre du bloc de détail, aligné sur les colonnes journalières, pour bien
        # distinguer visuellement le résumé décadaire ("...Bilan hydrique") du détail
        # jour par jour qui suit sur la même ligne d'en-tête.
        sheet.merge_cells(start_row=start + 1, start_column=NETWORK_SUMMARY_COLUMN_COUNT + 1, end_row=start + 1, end_column=total_columns)
        sheet.cell(start + 1, NETWORK_SUMMARY_COLUMN_COUNT + 1, "PLUIES JOURNALIERES (mm)")
        sheet.cell(start + 1, NETWORK_SUMMARY_COLUMN_COUNT + 1).font = Font(bold=True, italic=True, size=9)
        sheet.cell(start + 1, NETWORK_SUMMARY_COLUMN_COUNT + 1).alignment = Alignment(horizontal="center")
        sheet.append(NETWORK_HEADERS)
        header_row = sheet.max_row
        for department in departments:
            members = [station for station in stations if station.department == department]
            if not members:
                continue
            department_row = sheet.max_row + 1
            sheet.append([department])
            for cell in sheet[department_row][:total_columns]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="4E8B5D")
            for station in members:
                summary = summaries.get(station.id, {})
                row_number = sheet.max_row + 1
                normal = summary.get("normal_decade")
                etp = summary.get("etp")
                daily = list(summary.get("daily_values", []))[:10]
                daily += [None] * (10 - len(daily))
                sheet.append([station.name, summary.get("longitude", station.longitude), summary.get("latitude", station.latitude), f'=COUNTIF(N{row_number}:W{row_number},">0")', f'=COUNTIF(N{row_number}:W{row_number},">20")', f'=SUM(N{row_number}:W{row_number})', f'=F{row_number}-{normal}' if isinstance(normal, (int, float)) else summary.get("decade_deviation"), f'=IFERROR(F{row_number}/{normal},"")' if isinstance(normal, (int, float)) and normal else summary.get("normal_percentage"), summary.get("year_total"), summary.get("year_deviation"), summary.get("season_total"), summary.get("season_deviation"), f'=F{row_number}-{etp}' if isinstance(etp, (int, float)) else summary.get("water_balance")] + daily)
        # Repère visuel : fond légèrement différent sur les en-têtes du bloc détail
        # journalier pour qu'il ne se confonde pas avec la suite du bloc résumé.
        for cell in sheet[header_row][NETWORK_SUMMARY_COLUMN_COUNT:total_columns]:
            cell.fill = PatternFill("solid", fgColor="2F8F52")
        _style_table(sheet, header_row, [24, 13, 13, 14, 14, 18, 18, 18, 20, 18, 24, 18, 16] + [10] * 10, divider_col=NETWORK_SUMMARY_COLUMN_COUNT)
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
    sheet.row_dimensions[1].height = _title_row_height(15)
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
    normals_sheet = workbook.create_sheet("Tableau IV")
    normals_sheet.merge_cells("A1:J1")
    normals_sheet["A1"] = "TABLEAU IV - DONNEES CLIMATIQUES (Moyennes sur décade)"
    normals_sheet["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    normals_sheet["A1"].fill = PatternFill("solid", fgColor="0D472B")
    normals_sheet.row_dimensions[1].height = _title_row_height(14)
    normals_sheet.append(["STATIONS", "Tmin", "Tmax", "Tmoy", "+10cm", "+50cm", "Hum. min", "Hum. max", "Hum. moy", "Tension Vapeur", "Déficit"])
    for station in stations:
        values = climate.get(station.id, {})
        normal = values.get("normal") or {}
        current = [values.get(key) for key in ("tmin", "tmax", "tmean", "soil10", "soil50", "humidity_min", "humidity_max", "humidity_mean", "vapor_pressure", "deficit")]
        normals_sheet.append([station.name] + [value if value is not None else None for value in current])
        normals_sheet.append(["Ecart/Normale"] + [current[index] - normal[key] if isinstance(current[index], (int, float)) and isinstance(normal.get(key), (int, float)) else None for index, key in enumerate(("tmin", "tmax", "tmean", "soil10", "soil50", "hmin", "hmax", "hmean", "vapor_pressure", "deficit"))])
    _style_table(normals_sheet, 2, [22, 14, 14, 14, 14, 14, 14, 14, 14, 18, 14])
    return _download(workbook, f"DONNEES_CLIMATIQUES_{year}_{month:02d}_D{decade}.xlsx")


def _append_observations_table(sheet: openpyxl.worksheet.worksheet.Worksheet, year: int, month: int, decade: int, station: Station, rows: list[dict[str, object]], etp: float | None = None) -> None:
    """Append one full "Renseignements agro" table (title + 15 columns + total/moyenne/déficit) for a single station."""
    if sheet.max_row > 1:
        sheet.append([])
    start = sheet.max_row + 1
    sheet.merge_cells(start_row=start, start_column=1, end_row=start, end_column=15)
    sheet.cell(start, 1, "RENSEIGNEMENTS AGROMETEOROLOGIQUES")
    sheet.cell(start, 1).font = Font(bold=True, size=15, color="FFFFFF")
    sheet.cell(start, 1).fill = PatternFill("solid", fgColor="0D472B")
    sheet.cell(start, 1).alignment = Alignment(horizontal="center")
    sheet.row_dimensions[start].height = _title_row_height(15)
    sheet.merge_cells(start_row=start + 1, start_column=1, end_row=start + 1, end_column=15)
    sheet.cell(start + 1, 1, f"Station : {station.name} | Période : {decade}ère décade de {MONTHS[month - 1]} {year}")
    sheet.cell(start + 1, 1).alignment = Alignment(horizontal="center")
    sheet.append(OBSERVATIONS_HEADERS)
    header_row = sheet.max_row
    data_start = sheet.max_row + 1
    ordered = {int(row.get("jour", 0)): row for row in rows}
    for day in range(1, 11):
        row = ordered.get(day, {})
        tmin, tmax = row.get("temp_min"), row.get("temp_max")
        hmin, hmax = row.get("humidite_min"), row.get("humidite_max")
        row_number = sheet.max_row + 1
        sheet.append([
            day,
            row.get("pluie"),
            tmin,
            tmax,
            f"=IF(COUNT(C{row_number}:D{row_number})=2,AVERAGE(C{row_number}:D{row_number}),\"\")",
            row.get("temp_10cm"),
            row.get("temp_50cm"),
            row.get("vent_moyen"),
            row.get("vent_max"),
            row.get("insolation"),
            hmin,
            hmax,
            f"=IF(COUNT(K{row_number}:L{row_number})=2,0.6*K{row_number}+0.4*L{row_number},\"\")",
            row.get("tension_vapeur"),
            row.get("evapo_bac_a"),
        ])
    data_end = sheet.max_row
    sheet.append([
        "Total",
        f'=IFERROR(SUM(B{data_start}:B{data_end}),"")',
        "", "", "", "", "", "", "",
        f'=IFERROR(SUM(J{data_start}:J{data_end}),"")',
        "", "", "", "",
        f'=IFERROR(SUM(O{data_start}:O{data_end}),"")',
    ])
    sheet.append([
        "Moyenne",
        f'=IFERROR(AVERAGE(B{data_start}:B{data_end}),"")',
        f'=IFERROR(AVERAGE(C{data_start}:C{data_end}),"")',
        f'=IFERROR(AVERAGE(D{data_start}:D{data_end}),"")',
        f'=IFERROR(AVERAGE(E{data_start}:E{data_end}),"")',
        f'=IFERROR(AVERAGE(F{data_start}:F{data_end}),"")',
        f'=IFERROR(AVERAGE(G{data_start}:G{data_end}),"")',
        f'=IFERROR(AVERAGE(H{data_start}:H{data_end}),"")',
        f'=IFERROR(AVERAGE(I{data_start}:I{data_end}),"")',
        f'=IFERROR(AVERAGE(J{data_start}:J{data_end}),"")',
        f'=IFERROR(AVERAGE(K{data_start}:K{data_end}),"")',
        f'=IFERROR(AVERAGE(L{data_start}:L{data_end}),"")',
        f'=IFERROR(AVERAGE(M{data_start}:M{data_end}),"")',
        f'=IFERROR(AVERAGE(N{data_start}:N{data_end}),"")',
        f'=IFERROR(AVERAGE(O{data_start}:O{data_end}),"")',
    ])
    moyenne_row = sheet.max_row
    # Le déficit (ETP - tension de vapeur) est une valeur unique pour toute la décade
    # (l'ETP n'est saisie qu'une fois par décade) : on l'ajoute donc comme une ligne
    # sous "Moyenne", dans la colonne "Tension vapeur", plutôt que comme une colonne
    # répétée jour par jour.
    deficit_formula = f'=IFERROR({etp}-{OBSERVATIONS_VAPOR_PRESSURE_COLUMN}{moyenne_row},"")' if etp is not None else ""
    sheet.append(["Déficit"] + [""] * 12 + [deficit_formula, ""])
    _style_table(sheet, header_row, [10, 12, 12, 12, 12, 14, 14, 14, 14, 14, 12, 12, 12, 16, 14])
    for row_index in (sheet.max_row - 2, sheet.max_row - 1, sheet.max_row):
        for cell in sheet[row_index]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="4E8B5D")


def build_observations_export(year: int, month: int, decade: int, stations: Iterable[Station], rows_by_station: dict[str, list[dict[str, object]]], etp_by_station: dict[str, float | None] | None = None) -> tuple[BytesIO, str]:
    """Export one "Renseignements agro" table per station, all in a single workbook.

    ``stations`` should contain every station of the "Renseignements agrométéorologiques"
    section (the principal stations), and ``rows_by_station`` maps each station id to its
    list of daily observation rows for the requested decade. ``etp_by_station`` maps each
    station id to the ETP saisie pour la décade (utilisée pour la ligne "Déficit").
    """
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Renseignements agro"
    stations = list(stations)
    etp_by_station = etp_by_station or {}
    for station in stations:
        etp = etp_by_station.get(station.id)
        _append_observations_table(sheet, year, month, decade, station, rows_by_station.get(station.id, []), etp if isinstance(etp, (int, float)) else None)
    sheet.append([])
    sheet.append(["* L'humidité moyenne (Umoy) est calculée à partir de la température moyenne."])
    sheet.append(["* Déficit = ETP - tension de vapeur moyenne (valeur unique pour la décade, sous la ligne Moyenne)."])
    sheet.append(["* Les données manquantes sont codées par -."])
    for row_index in range(sheet.max_row - 2, sheet.max_row + 1):
        for cell in sheet[row_index]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="D9EAD3")
    return _download(workbook, f"RENSEIGNEMENTS_AGRO_{year}_{month:02d}_D{decade}.xlsx")
