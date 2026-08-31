from datetime import date
import unittest

from app.agro.calculations import build_summary, grouped_stations, rain_statistics, resolve_etp_station, rolling_totals, season_contains
from app.agro.models import AstronomicalConstant, DailyAgro, DailyRain, EditableDecadeValues, RainfallNormal, Station
from app.agro.registry import H10_BY_STATION, canonical_stations


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

    def test_rolling_year_total_uses_two_months(self) -> None:
        station = Station("p", "Parakou", "Borgou", "Parakou")
        history = [DailyRain("p", date(2026, 1, 5), 10), DailyRain("p", date(2026, 2, 5), 20), DailyRain("p", date(2025, 12, 5), 999)]
        self.assertEqual(rolling_totals(station, date(2026, 2, 10), history), (30, None))

    def test_season_change_dates(self) -> None:
        north = Station("n", "Parakou", "Borgou", "Parakou")
        south = Station("s", "Cotonou", "Littoral", "Cotonou")
        self.assertEqual(rolling_totals(north, date(2026, 4, 2), [DailyRain("n", date(2026, 3, 31), 1), DailyRain("n", date(2026, 4, 2), 2)])[1], 2)
        self.assertEqual(rolling_totals(south, date(2026, 9, 2), [DailyRain("s", date(2026, 7, 31), 3), DailyRain("s", date(2026, 8, 1), 4), DailyRain("s", date(2026, 9, 2), 5)])[1], 5)

    def test_grouping_order_and_invalid_department(self) -> None:
        stations = [Station("a", "A", "Zou", "A"), Station("b", "B", "Alibori", "B")]
        grouped = grouped_stations(stations)
        self.assertEqual([(block, department) for block, department, _ in grouped[:5]], [("Tableau 1", "Alibori"), ("Tableau 1", "Atacora"), ("Tableau 1", "Borgou"), ("Tableau 1", "Donga"), ("Tableau 2", "Collines")])
        with self.assertRaises(ValueError): grouped_stations([Station("x", "X", "Inconnu", "X")])

    def test_secondary_etp_attachment(self) -> None:
        cotonou = Station("c", "Cotonou", "Littoral", "Cotonou", principal=True)
        come = Station("co", "Comé", "Mono", "Comé", etp_station_id="c")
        unknown = Station("u", "U", "Mono", "U")
        self.assertEqual(resolve_etp_station(come, {"c": cotonou}), cotonou)
        self.assertIsNone(resolve_etp_station(unknown, {"c": cotonou}))

    def test_canonical_registry_contains_all_resa_stations(self) -> None:
        stations = canonical_stations()
        self.assertGreater(len(stations), 100)
        self.assertEqual([station.name for station in stations if station.principal], ["Kandi", "Parakou", "Natitingou", "Savè", "Bohicon", "Cotonou"])
        come = next(station for station in stations if station.name == "Comè")
        self.assertEqual(come.etp_station_id, "cotonou")

    def test_h10_constants_for_principal_stations(self) -> None:
        self.assertEqual(H10_BY_STATION, {
            "cotonou": 124.0,
            "bohicon": 125.0,
            "savè": 125.0,
            "parakou": 126.0,
            "natitingou": 126.0,
            "kandi": 127.0,
        })

    def test_global_radiation_uses_fraction_without_percent_scale(self) -> None:
        summary = build_summary(
            Station("cotonou", "Cotonou", "Littoral", "Cotonou", principal=True),
            2026,
            8,
            1,
            [],
            [],
            astronomical=AstronomicalConstant("cotonou", "1", 124, 3948.8097, 0.29, 0.42),
            agro_days=[DailyAgro("cotonou", date(2026, 8, 1), sunshine=62)],
        )
        self.assertEqual(summary.insolation_fraction, 50)
        self.assertAlmostEqual(summary.global_radiation, 3948.8097 * (0.29 + 0.42 * 0.5))

    def test_table_two_and_three_station_order(self) -> None:
        grouped = grouped_stations(canonical_stations())
        table_two = [(department, [station.name for station in stations]) for block, department, stations in grouped if block == "Tableau 2"]
        table_three = [(department, [station.name for station in stations]) for block, department, stations in grouped if block == "Tableau 3"]
        self.assertEqual([department for department, _ in table_two], ["Collines", "Couffo", "Mono", "Zou"])
        self.assertEqual(table_two[0][1][0], "Agouna")
        self.assertEqual([department for department, _ in table_three], ["Atlantique", "Littoral", "Oueme", "Plateau"])
        self.assertEqual(table_three[0][1][0], "Allada")
        self.assertEqual(table_three[1][1][0], "Cotonou")


if __name__ == "__main__":
    unittest.main()
