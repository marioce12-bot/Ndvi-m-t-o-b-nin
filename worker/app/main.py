from __future__ import annotations

import hmac
import logging
import shutil
import tempfile
import time
import json
from datetime import date
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import db
from .config import get_settings
from .download import download_and_extract
from .notify import notify
from .memory import collect_memory, log_memory
from .pentades import list_available
from .processing import process_raster
from .render import render_map
from .storage import upload_image
from .agro.exports import build_climate_export, build_network_export
from .agro.calculations import build_summary, rain_statistics, rolling_totals
from .agro.models import AstronomicalConstant, DailyAgro, EditableDecadeValues, Station
from .agro.api_models import AgroRequest, EwEtpRequest, RainRequest, StationRequest
from .agro.registry import H10_BY_STATION, canonical_stations

COORDINATES = {}
try:
    COORDINATES = json.loads((Path(__file__).parents[1] / "data" / "station_coordinates.json").read_text(encoding="utf-8"))
except FileNotFoundError:
    pass
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
NORMALS = json.loads((Path(__file__).parents[1] / "data" / "rainfall_normals.json").read_text(encoding="utf-8")) if (Path(__file__).parents[1] / "data" / "rainfall_normals.json").exists() else {}


def _decade_code(month: int, decade: int) -> str:
    prefixes = {1: "j", 2: "f", 3: "ma", 4: "av", 5: "ma", 6: "ju", 7: "jl", 8: "a", 9: "s", 10: "o", 11: "n", 12: "d"}
    return f"{prefixes[month]}{decade}"

app = FastAPI(title="Plateforme NDVI Benin Worker", version="1.0.0")


def _avg(values: list[float | None]) -> float | None:
    filtered = [v for v in values if v is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def _build_principal_stations() -> list[Station]:
    started = time.perf_counter()
    db.ensure_principal_stations()
    docs = db.list_agro_stations(principale=True)
    stations: list[Station] = []
    for item in docs:
        stations.append(
            Station(
                id=str(item["id"]),
                name=str(item.get("name") or ""),
                department=str(item.get("department") or ""),
                locality=str(item.get("locality") or ""),
                principal=bool(item.get("principal")),
                etp_station_id=item.get("etp_station_id"),
                longitude=item.get("longitude") or COORDINATES.get(str(item["id"]), {}).get("longitude") or COORDINATES.get(str(item.get("name", "")), {}).get("longitude"),
                latitude=item.get("latitude") or COORDINATES.get(str(item["id"]), {}).get("latitude") or COORDINATES.get(str(item.get("name", "")), {}).get("latitude"),
            )
        )
    logger.info("agro stations initialization/list: %.0f ms, stations=%s", (time.perf_counter() - started) * 1000, len(stations))
    return stations


def _station_coordinates(station: Station) -> tuple[float | None, float | None]:
    values = COORDINATES.get(station.id) or COORDINATES.get(station.name) or {}
    return values.get("longitude"), values.get("latitude")


def _get_ew_etp_map(year: int, month: int, decade: int) -> dict[str, dict[str, object]]:
    return {str(item.get("station_id")): item for item in db.get_agro_ew_etp(year, month, decade)}


def _build_rain_export_summaries(year: int, month: int, decade: int) -> tuple[list[Station], dict[str, dict[str, object]]]:
    stations = canonical_stations()
    current_rain = db.list_agro_rain(year, month, decade)
    ew_etp = _get_ew_etp_map(year, month, decade)
    by_station: dict[str, list[float | None]] = {station.id: [] for station in stations}
    for row in current_rain:
        station_id = str(row.get("station_id"))
        if station_id in by_station:
            by_station[station_id].append(row.get("hauteur_mm"))
    summaries: dict[str, dict[str, object]] = {}
    for station in stations:
        values = by_station[station.id]
        rain_days, heavy_rain_days, maximum, total = rain_statistics(values)
        current_end = date(year, month, 10 if decade == 1 else 20 if decade == 2 else 31)
        year_total, season_total = rolling_totals(station, current_end, ())
        if total is not None:
            year_total += total
            season_total = (season_total or 0) + total if season_total is not None else None
        etp = ew_etp.get(station.id, {}).get("etp")
        normal = NORMALS.get(station.id, {}).get(_decade_code(month, decade), {})
        if not normal and month == 6:
            normal = NORMALS.get(station.id, {}).get(f"ju{decade}", {})
        normal_decade = normal.get("decade")
        normal_year = normal.get("annual")
        normal_season = normal.get("season")
        longitude, latitude = _station_coordinates(station)
        summaries[station.id] = {
            "rain_days": rain_days,
            "heavy_rain_days": heavy_rain_days,
            "rainfall_total": total,
            "year_total": year_total,
            "season_total": season_total,
            "decade_deviation": total - normal_decade if total is not None and isinstance(normal_decade, (int, float)) else None,
            "year_deviation": year_total - normal_year if isinstance(normal_year, (int, float)) else None,
            "season_deviation": season_total - normal_season if season_total is not None and isinstance(normal_season, (int, float)) else None,
            "water_balance": total - float(etp) if total is not None and isinstance(etp, (int, float)) else None,
            "longitude": longitude,
            "latitude": latitude,
        }
    return stations, summaries


def _build_station_daily_agro(year: int, month: int, decade: int, station_id: str) -> list[DailyAgro]:
    observations = db.list_agro_observations(year, month, decade, station_id)
    daily: list[DailyAgro] = []
    for row in observations:
        jour = int(row.get("jour"))
        daily.append(
            DailyAgro(
                station_id=station_id,
                observed_on=date(year, month, jour),
                rain_mm=row.get("pluie"),
                tmin=row.get("temp_min"),
                tmax=row.get("temp_max"),
                soil10=row.get("temp_10cm"),
                soil50=row.get("temp_50cm"),
                wind_mean=row.get("vent_moyen"),
                wind_max=row.get("vent_max"),
                sunshine=row.get("insolation"),
                humidity_min=row.get("humidite_min"),
                humidity_max=row.get("humidite_max"),
                vapor_pressure=row.get("tension_vapeur"),
                pan_evaporation=row.get("evapo_bac_a"),
            )
        )
    return daily


def _build_climate_for_principal_stations(year: int, month: int, decade: int) -> tuple[list[Station], dict[str, dict[str, object]]]:
    started = time.perf_counter()
    stations = _build_principal_stations()
    ew_etp_map = _get_ew_etp_map(year, month, decade)
    climate: dict[str, dict[str, object]] = {}

    for station in stations:
        daily_agro = _build_station_daily_agro(year, month, decade, station.id)
        sunshine_present = any(day.sunshine is not None for day in daily_agro)

        ew_doc = ew_etp_map.get(station.id, {})
        base_values = {k: v for k, v in ew_doc.items() if k not in {"id", "station_id"}}
        ew = ew_doc.get("ew")
        etp = ew_doc.get("etp")

        h10 = H10_BY_STATION.get(station.id)

        if not sunshine_present:
            radiation_fields = {"h10": h10, "insolation_fraction": None, "global_radiation": None}
        else:
            astronomical = AstronomicalConstant(station.id, str(decade), h10=h10, ra=3948.8097, angstrom_a=0.29, angstrom_b=0.42)
            editable = EditableDecadeValues(station.id, year, month, decade, ew=ew, etp=etp)
            summary = build_summary(
                station=station,
                year=year,
                month=month,
                decade=decade,
                current_rain=(),
                history_rain=(),
                rainfall_normal=None,
                editable=editable,
                astronomical=astronomical,
                agro_days=daily_agro,
            )
            radiation_fields = {
                "h10": summary.h10,
                "insolation_fraction": summary.insolation_fraction,
                "global_radiation": summary.global_radiation,
            }

        # Start from whatever is already persisted in agroEwEtp, then enforce
        # radiation fields computed from module-2 observations when available.
        climate_values: dict[str, object] = {
            **base_values,
            **radiation_fields,
            "ew": ew,
            "etp": etp,
            "tmin": base_values.get("tmin") if base_values.get("tmin") is not None else _avg([day.tmin for day in daily_agro]),
            "tmax": base_values.get("tmax") if base_values.get("tmax") is not None else _avg([day.tmax for day in daily_agro]),
            "tmean": base_values.get("tmean") if base_values.get("tmean") is not None else _avg([day.tmean for day in daily_agro]),
            "soil10": base_values.get("soil10") if base_values.get("soil10") is not None else _avg([day.soil10 for day in daily_agro]),
            "soil50": base_values.get("soil50") if base_values.get("soil50") is not None else _avg([day.soil50 for day in daily_agro]),
            "humidity_min": base_values.get("humidity_min") if base_values.get("humidity_min") is not None else _avg([day.humidity_min for day in daily_agro]),
            "humidity_max": base_values.get("humidity_max") if base_values.get("humidity_max") is not None else _avg([day.humidity_max for day in daily_agro]),
            "humidity_mean": base_values.get("humidity_mean") if base_values.get("humidity_mean") is not None else _avg([day.humidity_mean for day in daily_agro]),
            "vapor_pressure": base_values.get("vapor_pressure") if base_values.get("vapor_pressure") is not None else _avg([day.vapor_pressure for day in daily_agro]),
            "deficit": base_values.get("deficit")
            if base_values.get("deficit") is not None
            else (
                (ew - _avg([day.vapor_pressure for day in daily_agro]))
                if (ew is not None and _avg([day.vapor_pressure for day in daily_agro]) is not None)
                else None
            ),
            "sunshine_total": sum(day.sunshine for day in daily_agro if day.sunshine is not None) if sunshine_present else None,
            "wind_mean": base_values.get("wind_mean") if base_values.get("wind_mean") is not None else _avg([day.wind_mean for day in daily_agro]),
            "wind_max": base_values.get("wind_max") if base_values.get("wind_max") is not None else _avg([day.wind_max for day in daily_agro]),
            "pan_evaporation": base_values.get("pan_evaporation") if base_values.get("pan_evaporation") is not None else _avg([day.pan_evaporation for day in daily_agro]),
        }

        rain_docs = db.list_agro_rain(year, month, decade, station.id)
        rain_amounts = [float(r.get("hauteur_mm")) for r in rain_docs if r.get("hauteur_mm") is not None]
        if rain_amounts and etp is not None:
            climate_values["water_balance"] = sum(rain_amounts) - float(etp)
        else:
            climate_values["water_balance"] = None

        climate[station.id] = climate_values

    logger.info("agro climate build %s-%s dec=%s: %.0f ms, stations=%s", year, f"{month:02d}", decade, (time.perf_counter() - started) * 1000, len(stations))
    return stations, climate


class GenerateRequest(BaseModel):
    jobId: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    pentadeId: str = Field(pattern=r"^20\d{2}-P(?:0[1-9]|[1-6]\d|7[0-2])$")
    product: str = Field(pattern=r"^(ndvi|anomaly)$")
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    ownerId: str = Field(min_length=1, max_length=128)
    force: bool = False


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().api_key
    if not expected or not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _validate_period(year: int, month: int, decade: int) -> None:
    if not 1900 <= year <= 2100 or not 1 <= month <= 12 or decade not in (1, 2, 3):
        raise HTTPException(status_code=422, detail="Période invalide")


@app.get("/agro/stations", dependencies=[Depends(require_api_key)])
def agro_stations(principale: bool | None = None) -> dict[str, object]:
    db.ensure_principal_stations()
    return {"stations": db.list_agro_stations(principale)}


@app.post("/agro/stations", dependencies=[Depends(require_api_key)])
def save_agro_station(request: StationRequest) -> dict[str, object]:
    db.upsert_agro_station(request.model_dump())
    return {"station": next((station for station in db.list_agro_stations() if station["id"] == request.id), {"id": request.id, **request.model_dump(exclude={"id"})})}


@app.get("/agro/pluies", dependencies=[Depends(require_api_key)])
def agro_rains(year: int, month: int, decade: int) -> dict[str, object]:
    _validate_period(year, month, decade)
    return {"valeurs": db.list_agro_rain(year, month, decade)}


@app.post("/agro/pluies", dependencies=[Depends(require_api_key)])
def save_agro_rains(request: RainRequest) -> dict[str, object]:
    _validate_period(request.year, request.month, request.decade)
    payloads = [{"year": request.year, "month": request.month, "decade": request.decade, **value.model_dump()} for value in request.valeurs if value.hauteur_mm is not None]
    db.upsert_agro_rain(payloads)
    grouped: dict[str, list[float | None]] = {}
    for value in db.list_agro_rain(request.year, request.month, request.decade): grouped.setdefault(str(value["station_id"]), []).append(value.get("hauteur_mm"))
    return {"valeurs": db.list_agro_rain(request.year, request.month, request.decade), "calculs": {station: dict(zip(("nbjp_gt0", "nbjp_gt20", "max", "total"), rain_statistics(values))) for station, values in grouped.items()}}


@app.get("/agro/observations", dependencies=[Depends(require_api_key)])
def agro_observations(year: int, month: int, decade: int, station_id: str) -> dict[str, object]:
    _validate_period(year, month, decade)
    return {"valeurs": db.list_agro_observations(year, month, decade, station_id)}


@app.post("/agro/observations", dependencies=[Depends(require_api_key)])
def save_agro_observations(request: AgroRequest) -> dict[str, object]:
    _validate_period(request.year, request.month, request.decade)
    payloads = [{"year": request.year, "month": request.month, "decade": request.decade, "station_id": request.station_id, **value.model_dump()} for value in request.valeurs]
    db.upsert_agro_observations(payloads)
    values = db.list_agro_observations(request.year, request.month, request.decade, request.station_id)
    return {"valeurs": values, "totaux_moyennes": {"pluie": sum(v.get("pluie") or 0 for v in values), "insolation": sum(v.get("insolation") or 0 for v in values), "evapo_bac_a": sum(v.get("evapo_bac_a") or 0 for v in values), "temp_moy": sum((v.get("temp_min") + v.get("temp_max")) / 2 for v in values if v.get("temp_min") is not None and v.get("temp_max") is not None) / max(1, len(values))}}


@app.get("/agro/ew-etp", dependencies=[Depends(require_api_key)])
def agro_ew_etp(year: int, month: int, decade: int) -> dict[str, object]:
    _validate_period(year, month, decade)
    _, climate = _build_climate_for_principal_stations(year, month, decade)
    calculs = [
        {
            "station_id": station_id,
            "h10": values.get("h10"),
            "insolation_fraction": values.get("insolation_fraction"),
            "global_radiation": values.get("global_radiation"),
        }
        for station_id, values in climate.items()
    ]
    computed_numeric = sum(
        1
        for item in calculs
        if isinstance(item.get("h10"), (int, float))
        and isinstance(item.get("insolation_fraction"), (int, float))
        and isinstance(item.get("global_radiation"), (int, float))
    )
    logger.info(
        "agro/ew-etp %s-%s dec=%s: calculs=%s fully_computed=%s",
        year,
        f"{month:02d}",
        decade,
        len(calculs),
        computed_numeric,
    )
    return {"valeurs": db.get_agro_ew_etp(year, month, decade), "calculs": calculs}


@app.post("/agro/ew-etp", dependencies=[Depends(require_api_key)])
def save_agro_ew_etp(request: EwEtpRequest) -> dict[str, object]:
    _validate_period(request.year, request.month, request.decade)
    db.upsert_agro_ew_etp([{ "year": request.year, "month": request.month, "decade": request.decade, **value.model_dump()} for value in request.valeurs])
    _, climate = _build_climate_for_principal_stations(request.year, request.month, request.decade)
    calculs = [
        {
            "station_id": station_id,
            "h10": values.get("h10"),
            "insolation_fraction": values.get("insolation_fraction"),
            "global_radiation": values.get("global_radiation"),
        }
        for station_id, values in climate.items()
    ]
    return {"valeurs": db.get_agro_ew_etp(request.year, request.month, request.decade), "temperature_hygrometrie": [], "calculs": calculs}


@app.get("/agro/export/network.xlsx", dependencies=[Depends(require_api_key)])
def agro_network_export(year: int, month: int, decade: int) -> StreamingResponse:
    _validate_period(year, month, decade)
    stations, summaries = _build_rain_export_summaries(year, month, decade)
    stream, filename = build_network_export(year, month, decade, stations, summaries)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/agro/export/climate.xlsx", dependencies=[Depends(require_api_key)])
def agro_climate_export(year: int, month: int, decade: int) -> StreamingResponse:
    stations, climate = _build_climate_for_principal_stations(year, month, decade)
    computed_numeric = sum(
        1
        for values in climate.values()
        if isinstance(values.get("h10"), (int, float))
        and isinstance(values.get("insolation_fraction"), (int, float))
        and isinstance(values.get("global_radiation"), (int, float))
    )
    logger.info(
        "agro/export/climate.xlsx %s-%s dec=%s: stations=%s fully_computed=%s",
        year,
        f"{month:02d}",
        decade,
        len(list(stations)),
        computed_numeric,
    )
    stream, filename = build_climate_export(year, month, decade, stations, climate)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.post("/cron/run", status_code=202, dependencies=[Depends(require_api_key)])
def run_cron(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Start one automatic cycle from an external scheduler such as GitHub Actions."""
    from .cron import run

    background_tasks.add_task(run)
    return {"status": "accepted"}


@app.get("/pentades", dependencies=[Depends(require_api_key)])
def pentades(product: str = Query(pattern=r"^(ndvi|anomaly)$")) -> dict[str, list[dict[str, object]]]:
    return {"pentades": list_available(product)}


def _run_pipeline(request: GenerateRequest, label: str, url: str, notify_failure: bool = True) -> bool:
    workdir = Path(tempfile.mkdtemp(prefix="ndvi-benin-", dir="/tmp"))
    succeeded = False
    try:
        log_memory(f"{request.jobId}:before_download")
        logger.info("Job %s: processing", request.jobId)
        db.mark_processing(request.jobId)
        db.update_progress(request.jobId, 5, "Téléchargement des données USGS")
        raster = download_and_extract(url, workdir)
        log_memory(f"{request.jobId}:after_download")
        db.update_progress(request.jobId, 10, "Données raster téléchargées")
        log_memory(f"{request.jobId}:before_clip")
        values, transform = process_raster(raster, request.product, Path(__file__).parents[1] / "data" / "benin_adm1.geojson")
        log_memory(f"{request.jobId}:after_clip")
        db.update_progress(request.jobId, 40, "Découpe sur le Bénin")
        output = workdir / f"{request.product}_{request.pentadeId}.jpg"
        year, pentade_num = request.pentadeId.split("-P")
        log_memory(f"{request.jobId}:before_render")
        render_map(values, transform, request.product, int(year), int(pentade_num), Path(__file__).parents[1] / "data" / "benin_adm1.geojson", output, Path(__file__).parents[1] / "assets" / "logo.webp")
        log_memory(f"{request.jobId}:after_render")
        db.update_progress(request.jobId, 75, "Génération de la carte")
        del values
        collect_memory(f"{request.jobId}:after_release_raster")
        log_memory(f"{request.jobId}:before_upload")
        image_url, thumbnail_url = upload_image(output, f"{request.product}_{request.pentadeId}")
        log_memory(f"{request.jobId}:after_upload")
        db.update_progress(request.jobId, 95, "Envoi de l'image")
        db.mark_done(request.jobId, image_url, thumbnail_url)
        notify("NDVI anomalie" if request.product == "anomaly" else "NDVI", label, image_url, "Carte prête", request.email)
        logger.info("Job %s: done", request.jobId)
        succeeded = True
    except Exception as error:
        logger.exception("Job %s: failed", request.jobId)
        try:
            db.mark_error(request.jobId, str(error))
            if notify_failure:
                notify("NDVI anomalie" if request.product == "anomaly" else "NDVI", label, "", f"Échec : {str(error)[:500]}", request.email)
        except Exception:
            logger.exception("Job %s: unable to persist failure", request.jobId)
    finally:
        collect_memory(f"{request.jobId}:finally")
        shutil.rmtree(workdir, ignore_errors=True)
    return succeeded


@app.post("/generate", status_code=202, dependencies=[Depends(require_api_key)])
def generate(request: GenerateRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    try:
        available = next((item for item in list_available(request.product) if item["id"] == request.pentadeId), None)
    except Exception as error:
        logger.exception("Unable to list pentades for job %s", request.jobId)
        raise HTTPException(status_code=503, detail="Source USGS indisponible") from error
    if not available:
        raise HTTPException(status_code=404, detail="Pentade indisponible")
    label = str(available["label"])
    if not request.force:
        try:
            existing = db.find_done_job(request.product, request.pentadeId, request.ownerId)
        except Exception as error:
            logger.exception("Unable to query Firestore for job %s", request.jobId)
            raise HTTPException(status_code=503, detail="Firestore indisponible") from error
        if existing:
            data = existing.to_dict()
            try:
                db.update_job(request.jobId, email=request.email, status="done", imageUrl=data.get("imageUrl"), thumbnailUrl=data.get("thumbnailUrl"), completedAt=data.get("completedAt"), error=None)
            except Exception as error:
                logger.exception("Unable to update existing job %s", request.jobId)
                raise HTTPException(status_code=503, detail="Firestore indisponible") from error
            return {"status": "exists", "imageUrl": data.get("imageUrl", "")}
    try:
        db.create_pending(request.jobId, request.product, request.pentadeId, label, request.email, request.ownerId)
    except Exception as error:
        logger.exception("Unable to create Firestore job %s", request.jobId)
        raise HTTPException(status_code=503, detail="Impossible de créer le job dans Firestore") from error
    background_tasks.add_task(_run_pipeline, request, label, str(available["url"]))
    return {"status": "accepted"}


@app.post("/replay", status_code=202, dependencies=[Depends(require_api_key)])
def replay(request: GenerateRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    """Replay a pentade manually; force bypasses the completed-job deduplication."""
    request.force = True
    return generate(request, background_tasks)
