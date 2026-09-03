def build_observations_export(year: int, month: int, decade: int, station: Station, rows: list[dict[str, object]]) -> tuple[BytesIO, str]:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Renseignements agro"
    sheet.merge_cells("A1:O1")
    sheet["A1"] = "RENSEIGNEMENTS AGROMETEOROLOGIQUES"
    sheet["A1"].font = Font(bold=True, size=15, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor="0D472B")
    sheet["A1"].alignment = Alignment(horizontal="center")
    sheet.merge_cells("A2:O2")
    sheet["A2"] = f"Station : {station.name} | Période : {decade}ère décade de {MONTHS[month - 1]} {year}"
    sheet["A2"].alignment = Alignment(horizontal="center")
    sheet.append([])
    headers = ["Jour", "Pluie", "Tmin", "Tmax", "T moy", "Temp. 10cm", "Temp. 50cm", "Vent moyen", "Vent maxi", "Insolation", "Hum. min", "Hum. max", "Hum. moy", "Tension vapeur", "Évapo. bac"]
    sheet.append(headers)
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
        f"=SUM(B{data_start}:B{data_end})",
        "", "", "", "", "", "", "",
        f"=SUM(J{data_start}:J{data_end})",
        "", "", "", "",
        f"=SUM(O{data_start}:O{data_end})",
    ])
    sheet.append([
        "Moyenne",
        f"=AVERAGE(B{data_start}:B{data_end})",
        f"=AVERAGE(C{data_start}:C{data_end})",
        f"=AVERAGE(D{data_start}:D{data_end})",
        f"=AVERAGE(E{data_start}:E{data_end})",
        f"=AVERAGE(F{data_start}:F{data_end})",
        f"=AVERAGE(G{data_start}:G{data_end})",
        f"=AVERAGE(H{data_start}:H{data_end})",
        f"=AVERAGE(I{data_start}:I{data_end})",
        f"=AVERAGE(J{data_start}:J{data_end})",
        f"=AVERAGE(K{data_start}:K{data_end})",
        f"=AVERAGE(L{data_start}:L{data_end})",
        f"=AVERAGE(M{data_start}:M{data_end})",
        f"=AVERAGE(N{data_start}:N{data_end})",
        f"=AVERAGE(O{data_start}:O{data_end})",
    ])
    _style_table(sheet, 4, [10, 12, 12, 12, 12, 14, 14, 14, 14, 14, 12, 12, 12, 16, 14])
    for row in (sheet.max_row - 1, sheet.max_row):
        for cell in sheet[row]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="4E8B5D")
    sheet.auto_filter.ref = f"A4:O{sheet.max_row}"
    sheet.append([])
    sheet.append(["* L'humidité moyenne (Umoy) est calculée à partir de la température moyenne."])
    sheet.append(["* Déficit de saturation = ew - tension de vapeur moyenne."])
    sheet.append(["* Les données manquantes sont codées par -."])
    for row_index in range(sheet.max_row - 2, sheet.max_row + 1):
        for cell in sheet[row_index]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="D9EAD3")
    return _download(workbook, f"RENSEIGNEMENTS_AGRO_{station.id}_{year}_{month:02d}_D{decade}.xlsx")
