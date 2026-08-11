from datetime import date
import unittest

from app.pentades import pentade_label, pentade_to_dates


class PentadeTests(unittest.TestCase):
    def test_pentade_to_dates_first_and_last_slots(self) -> None:
        self.assertEqual(pentade_to_dates(2025, 1), (date(2025, 1, 1), date(2025, 1, 5)))
        self.assertEqual(pentade_to_dates(2025, 6), (date(2025, 1, 26), date(2025, 1, 31)))
        self.assertEqual(pentade_to_dates(2025, 72), (date(2025, 12, 26), date(2025, 12, 31)))

    def test_pentade_label_is_french(self) -> None:
        self.assertEqual(pentade_label(2025, 34), "16-20 juin 2025")

    def test_pentade_number_is_bounded(self) -> None:
        for num in (0, 73):
            with self.assertRaises(ValueError):
                pentade_to_dates(2025, num)


if __name__ == "__main__":
    unittest.main()
