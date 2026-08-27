from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class RainValue(BaseModel):
    station_id: str = Field(min_length=1)
    jour: int = Field(ge=1, le=31)
    hauteur_mm: Optional[float] = None


class RainRequest(BaseModel):
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    decade: int = Field(ge=1, le=3)
    valeurs: list[RainValue]


class AgroValue(BaseModel):
    jour: int = Field(ge=1, le=31)
    pluie: Optional[float] = None
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    temp_10cm: Optional[float] = None
    temp_50cm: Optional[float] = None
    vent_moyen: Optional[float] = None
    vent_max: Optional[float] = None
    insolation: Optional[float] = None
    humidite_min: Optional[float] = None
    humidite_max: Optional[float] = None
    tension_vapeur: Optional[float] = None
    evapo_bac_a: Optional[float] = None


class AgroRequest(BaseModel):
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    decade: int = Field(ge=1, le=3)
    station_id: str = Field(min_length=1)
    valeurs: list[AgroValue]


class EwEtpValue(BaseModel):
    station_id: str = Field(min_length=1)
    ew: Optional[float] = None
    etp: Optional[float] = None


class EwEtpRequest(BaseModel):
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    decade: int = Field(ge=1, le=3)
    valeurs: list[EwEtpValue]
