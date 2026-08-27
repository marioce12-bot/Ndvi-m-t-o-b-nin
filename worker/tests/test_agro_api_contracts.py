import unittest
from unittest.mock import patch

from app.agro.api_models import AgroRequest, EwEtpRequest, RainRequest


class AgroApiContractTests(unittest.TestCase):
    def test_period_validation_model(self) -> None:
        request = RainRequest(year=2026, month=8, decade=1, valeurs=[])
        self.assertEqual(request.decade, 1)
        with self.assertRaises(ValueError): RainRequest(year=2026, month=8, decade=4, valeurs=[])

    def test_partial_rain_upsert_payload_is_allowed(self) -> None:
        request = RainRequest(year=2026, month=8, decade=1, valeurs=[{"station_id": "a", "jour": 1, "hauteur_mm": 12.5}])
        self.assertEqual(request.valeurs[0].station_id, "a")

    def test_agro_calculated_fields_are_not_input_fields(self) -> None:
        request = AgroRequest(year=2026, month=8, decade=1, station_id="cotonou", valeurs=[{"jour": 1, "temp_min": 20, "temp_max": 30, "humidite_min": 60, "humidite_max": 90}])
        self.assertFalse(hasattr(request.valeurs[0], "temp_moy"))
        self.assertFalse(hasattr(request.valeurs[0], "humidite_moy"))

    def test_ew_etp_is_independent_payload(self) -> None:
        request = EwEtpRequest(year=2026, month=8, decade=1, valeurs=[{"station_id": "cotonou", "ew": 30, "etp": 42}])
        self.assertEqual(request.valeurs[0].etp, 42)


if __name__ == "__main__":
    unittest.main()
