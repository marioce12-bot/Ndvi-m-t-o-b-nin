from io import BytesIO
import unittest

import openpyxl

from app.agro.exports import build_climate_export, build_network_export
from app.agro.models import Station
from app.agro.registry import canonical_stations


class AgroExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stations = [Station("a", "Station A", "Alibori", "A"), Station("c", "Station C", "Littoral", "C")]

    def test_network_export_is_independent_and_downloadable(self) -> None:
        stream, filename = build_network_export(2026, 8, 1, self.stations, {"a": {"rain_days": 2}})
        workbook = openpyxl.load_workbook(stream)
        self.assertEqual(filename, "RESA-1_AOUT_2026.xlsx")
        self.assertEqual(workbook.sheetnames, ["Réseau pluviométrique"])
        self.assertEqual(workbook.active[2][0].value, "RESEAU PLUVIOMETRIQUE")

    def test_climate_export_keeps_missing_values_blank(self) -> None:
        stream, filename = build_climate_export(2026, 8, 1, self.stations, {"a": {"etp": 12}})
        workbook = openpyxl.load_workbook(stream)
        self.assertEqual(filename, "DONNEES_CLIMATIQUES-1_AOUT_2026.xlsx")
        self.assertEqual(workbook.active[4][1].value, None)
        self.assertTrue(any(str(cell.value).startswith("TABLEAU V-a") for row in workbook.active.iter_rows() for cell in row))

    def test_network_export_contains_all_three_blocks(self) -> None:
        stream, _ = build_network_export(2026, 8, 1, canonical_stations(), {})
        sheet = openpyxl.load_workbook(stream).active
        values = [cell.value for row in sheet.iter_rows() for cell in row]
        self.assertIn("DEPARTEMENTS : Alibori, Atacora, Borgou, Donga", values)
        self.assertIn("DEPARTEMENTS : Collines, Couffo, Mono, Zou", values)
        self.assertIn("DEPARTEMENTS : Atlantique, Littoral, Oueme, Plateau", values)
        self.assertIn("Agouna", values)
        self.assertIn("Allada", values)


if __name__ == "__main__":
    unittest.main()
