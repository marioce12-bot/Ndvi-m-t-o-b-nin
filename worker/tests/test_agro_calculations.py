from datetime import date
import unittest

from app.agro.calculations import build_summary, rain_statistics, season_contains
from app.agro.models import AstronomicalConstant, DailyAgro, DailyRain, EditableDecadeValues, RainfallNormal, Station


class AgroCalculationTests(unittest.TestCase):
    def test_rain_statistics_match_resa_thresholds(self) -> None:
        self.assertEqual(rain_statistics([None, 0, 0.5, 1, 20, 20.1]), (4, 1, 20.1, 41.6))

    def test_humidity_mean_uses_official_weighting(self) -> None:
        day = DailyAgro("cotonou", date(2026, 8, 1), humidity_min=60, humidity_max=90, tmin=20, tmax=30)
        self.assertEqual(day.tmean, 25)
        self.assertEqual(day.humidity_mean, 72)

    def test_seasons(self) -> None:
        north = Station("n", "Parakou", "Borgou", "Parakou")
        south = Station("s", "Cotonou", "Littoral", "Cotonou")
        self.assertTrue(season_contains(north, 4))
        self.assertFalse(season_contains(north, 3))
        self.assertTrue(season_contains(south, 3))
        self.assertTrue(season_contains(south, 9))
        self.assertFalse(season_contains(south, 8))

    def test_summary_includes_normals_water_balance_and_radiation(self) -> None:
        station = Station("p", "Parakou", "Borgou", "Parakou", principal=True)
        summary = build_summary(
            station, 2026, 8, 1,
            [DailyRain("p", date(2026, 8, 1), 10), DailyRain("p", date(2026, 8, 2), 25)],
            [],
            RainfallNormal("p", "a1", 20, 100, 80),
            EditableDecadeValues("p", 2026, 8, 1, ew=30, etp=12),
            AstronomicalConstant("p", "a1", 100, 400, 0.25, 0.45),
            [DailyAgro("p", date(2026, 8, 1), sunshine=50)],
        )
        self.assertEqual(summary.rain_days, 2)
        self.assertEqual(summary.heavy_rain_days, 1)
        self.assertEqual(summary.water_balance, 23)
        self.assertEqual(summary.insolation_fraction, 50)
        self.assertEqual(summary.global_radiation, 190)


if __name__ == "__main__":
    unittest.main()
