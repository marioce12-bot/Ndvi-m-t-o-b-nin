"""Domain models for the decade agrometeorological bulletin."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    department: str
    locality: str
    principal: bool = False
    etp_station_id: Optional[str] = None


@dataclass(frozen=True)
class RainfallNormal:
    station_id: str
    decade_code: str
    decade_total: Optional[float]
    annual_total: Optional[float]
    season_total: Optional[float]


@dataclass(frozen=True)
class AgroNormal:
    station_id: str
    decade_code: str
    tmin: Optional[float]
    tmax: Optional[float]
    tmean: Optional[float]
    humidity_min: Optional[float]
    humidity_max: Optional[float]
    humidity_mean: Optional[float]
    sunshine: Optional[float]


@dataclass(frozen=True)
class AstronomicalConstant:
    station_id: str
    decade_code: str
    h10: Optional[float]
    ra: Optional[float]
    angstrom_a: float
    angstrom_b: float


@dataclass(frozen=True)
class DailyRain:
    station_id: str
    observed_on: date
    amount_mm: Optional[float]


@dataclass(frozen=True)
class DailyAgro:
    station_id: str
    observed_on: date
    rain_mm: Optional[float] = None
    tmin: Optional[float] = None
    tmax: Optional[float] = None
    soil10: Optional[float] = None
    soil50: Optional[float] = None
    wind_mean: Optional[float] = None
    wind_max: Optional[float] = None
    sunshine: Optional[float] = None
    humidity_min: Optional[float] = None
    humidity_max: Optional[float] = None
    vapor_pressure: Optional[float] = None
    pan_evaporation: Optional[float] = None

    @property
    def tmean(self) -> Optional[float]:
        if self.tmin is None or self.tmax is None:
            return None
        return (self.tmin + self.tmax) / 2

    @property
    def humidity_mean(self) -> Optional[float]:
        if self.humidity_min is None or self.humidity_max is None:
            return None
        return 0.6 * self.humidity_min + 0.4 * self.humidity_max


@dataclass
class EditableDecadeValues:
    station_id: str
    year: int
    month: int
    decade: int
    ew: Optional[float] = None
    etp: Optional[float] = None


@dataclass
class DecadeSummary:
    station_id: str
    year: int
    month: int
    decade: int
    rain_days: int = 0
    heavy_rain_days: int = 0
    rainfall_total: Optional[float] = None
    rainfall_max: Optional[float] = None
    normal_decade: Optional[float] = None
    year_total: Optional[float] = None
    year_deviation: Optional[float] = None
    season_total: Optional[float] = None
    normal_season: Optional[float] = None
    season_deviation: Optional[float] = None
    water_balance: Optional[float] = None
    h10: Optional[float] = None
    insolation_fraction: Optional[float] = None
    global_radiation: Optional[float] = None
    ew: Optional[float] = None
    etp: Optional[float] = None
