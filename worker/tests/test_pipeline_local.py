from datetime import date
import unittest

from app.pentades import pentade_for_date, pentade_label, pentade_to_dates


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

    def test_last_slot_uses_actual_month_length(self) -> None:
        self.assertEqual(pentade_to_dates(2024, 12)[1], date(2024, 2, 29))
        self.assertEqual(pentade_to_dates(2025, 18)[1], date(2025, 3, 31))
        self.assertEqual(pentade_to_dates(2025, 30)[1], date(2025, 5, 31))

    def test_expected_pentade_waits_for_end_plus_delay(self) -> None:
        self.assertEqual(pentade_for_date(date(2025, 2, 1)), 6)
        self.assertEqual(pentade_for_date(date(2025, 3, 2)), 12)
        self.assertEqual(pentade_for_date(date(2025, 8, 16)), 45)
        self.assertEqual(pentade_for_date(date(2026, 8, 16)), 45)


if __name__ == "__main__":
    unittest.main()
