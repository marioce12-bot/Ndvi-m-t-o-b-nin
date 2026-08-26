from pathlib import Path
import unittest

from app.rainfall import parse_agro_xls, parse_decades_xls


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


if __name__ == "__main__":
    unittest.main()
