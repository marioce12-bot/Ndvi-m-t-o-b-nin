from pathlib import Path
import unittest

from app.rainfall import parse_agro_normals_xls, parse_agro_xls, parse_decades_xls, parse_rainfall_normals_xls


DOWNLOADS = Path(r"C:\Users\DELL\Downloads")


class RainfallImportTests(unittest.TestCase):
    def test_decades_reference_workbook(self) -> None:
        path = DOWNLOADS / "DECADES AOUT 2026.xlsx"
        if not path.exists():
            self.skipTest("Reference workbook is not available")
        parsed = __import__("app.rainfall", fromlist=["parse_decades_xlsx"]).parse_decades_xlsx(path.read_bytes(), (2026, 8, 1))
        self.assertEqual((parsed.year, parsed.month, parsed.decade), (2026, 8, 1))
        self.assertGreater(len(parsed.rows), 100)

    def test_agro_reference_workbook(self) -> None:
        path = DOWNLOADS / "Renseignements Agro 1ère décade AOUT  2026.xls"
        if not path.exists():
            self.skipTest("Reference workbook is not available")
        parsed = parse_agro_xls(path.read_bytes())
        self.assertEqual((parsed.year, parsed.month, parsed.decade), (2026, 8, 1))
        self.assertGreaterEqual(len(parsed.rows), 60)
        self.assertEqual(parsed.rows[0]["station"], "COTONOU")

    def test_separate_normals_references(self) -> None:
        rain_path = next(DOWNLOADS.glob("RESA-01*.xls"), None)
        agro_path = next(DOWNLOADS.glob("Renseignements Agro*.xls"), None)
        if not rain_path or not agro_path:
            self.skipTest("Reference workbooks are not available")
        rain = parse_rainfall_normals_xls(rain_path.read_bytes())
        agro = parse_agro_normals_xls(agro_path.read_bytes())
        self.assertTrue(rain)
        self.assertTrue(agro)
        self.assertTrue(all(row["source"] == "rainfall" for row in rain))
        self.assertTrue(all(row["source"] == "agro" for row in agro))


if __name__ == "__main__":
    unittest.main()
