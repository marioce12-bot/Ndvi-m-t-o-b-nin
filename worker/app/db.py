"""Supabase persistence adapter used by the worker."""

from __future__ import annotations

from functools import lru_cache
from datetime import datetime, timezone

from supabase import create_client

from .config import get_settings


@lru_cache
def get_client():
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY sont absents")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rows(response) -> list[dict[str, object]]:
    return list(response.data or [])


def get_job(job_id: str):
    return get_client().table("jobs").select("*").eq("id", job_id).maybe_single().execute()


def list_agro_stations(principale: bool | None = None) -> list[dict[str, object]]:
    query = get_client().table("agro_stations").select("*")
    if principale is not None:
        query = query.eq("principal", principale)
    return _rows(query.execute())


def list_all_agro_stations(principale: bool | None = None) -> list[dict[str, object]]:
    return list_agro_stations(principale)


def ensure_principal_stations() -> None:
    from .agro.registry import station_documents
    values = [{**station, "created_at": _now()} for station in station_documents()]
    if values:
        get_client().table("agro_stations").upsert(values, on_conflict="id").execute()


def upsert_agro_station(value: dict[str, object]) -> None:
    payload = dict(value)
    payload["created_at"] = _now()
    get_client().table("agro_stations").upsert(payload, on_conflict="id").execute()


def delete_agro_station(station_id: str) -> None:
    get_client().table("agro_stations").delete().eq("id", station_id).eq("principal", False).execute()


def list_agro_rain(year: int, month: int, decade: int, station_id: str | None = None) -> list[dict[str, object]]:
    query = get_client().table("agro_rain_daily").select("*").eq("year", year).eq("month", month).eq("decade", decade)
    if station_id:
        query = query.eq("station_id", station_id)
    return _rows(query.execute())


def list_agro_rain_until(year: int, month: int, decade: int) -> list[dict[str, object]]:
    end_day = 10 if decade == 1 else 20 if decade == 2 else 31
    rows = _rows(get_client().table("agro_rain_daily").select("*").eq("year", year).eq("month", month).execute())
    return [row for row in rows if int(row.get("month", 0)) < month or (int(row.get("month", 0)) == month and int(row.get("jour", 0)) <= end_day)]


def upsert_agro_rain(payloads: list[dict[str, object]]) -> None:
    if payloads:
        rows = [{**value, "id": f"{value['station_id']}-{value['year']}-{int(value['month']):02d}-{value['decade']}-{value['jour']}"} for value in payloads]
        get_client().table("agro_rain_daily").upsert(rows, on_conflict="station_id,year,month,decade,jour").execute()


def list_agro_observations(year: int, month: int, decade: int, station_id: str) -> list[dict[str, object]]:
    return _rows(get_client().table("agro_observations").select("*").eq("year", year).eq("month", month).eq("decade", decade).eq("station_id", station_id).execute())


def upsert_agro_observations(payloads: list[dict[str, object]]) -> None:
    if payloads:
        rows = [{**value, "id": f"{value['station_id']}-{value['year']}-{int(value['month']):02d}-{value['decade']}-{value['jour']}"} for value in payloads]
        get_client().table("agro_observations").upsert(rows, on_conflict="station_id,year,month,decade,jour").execute()


def get_agro_ew_etp(year: int, month: int, decade: int) -> list[dict[str, object]]:
    return _rows(get_client().table("agro_ew_etp").select("*").eq("year", year).eq("month", month).eq("decade", decade).execute())


def upsert_agro_ew_etp(payloads: list[dict[str, object]]) -> None:
    if payloads:
        rows = [{**value, "id": f"{value['station_id']}-{value['year']}-{int(value['month']):02d}-{value['decade']}"} for value in payloads]
        get_client().table("agro_ew_etp").upsert(rows, on_conflict="station_id,year,month,decade").execute()


def list_users() -> list[tuple[str, str]]:
    users = get_client().auth.admin.list_users().users
    return [(user.id, user.email) for user in users if user.email]


def save_pentades(product: str, pentades: list[dict[str, object]]) -> None:
    get_client().table("pentade_catalog").upsert({"product": product, "pentades": pentades, "updated_at": _now()}, on_conflict="product").execute()


def find_done_job(product: str, pentade_id: str, owner_id: str | None):
    query = get_client().table("jobs").select("*").eq("product", product).eq("pentade_id", pentade_id).eq("status", "done")
    query = query.is_("owner_id", "null") if owner_id is None else query.eq("owner_id", owner_id)
    response = query.limit(1).execute()
    return response.data[0] if response.data else None


def create_pending(job_id: str, product: str, pentade_id: str, label: str, email: str, owner_id: str | None) -> None:
    get_client().table("jobs").upsert({"id": job_id, "owner_id": owner_id, "product": product, "pentade_id": pentade_id, "label": label, "email": email, "status": "pending", "progress": 0, "step": "En attente", "created_at": _now()}, on_conflict="id").execute()


def update_job(job_id: str, **fields) -> None:
    mapping = {"imageUrl": "image_url", "thumbnailUrl": "thumbnail_url", "ownerId": "owner_id", "pentadeId": "pentade_id", "startedAt": "started_at", "completedAt": "completed_at"}
    payload = {mapping.get(key, key): value.isoformat() if isinstance(value, datetime) else value for key, value in fields.items()}
    get_client().table("jobs").update(payload).eq("id", job_id).execute()


def mark_processing(job_id: str) -> None:
    update_job(job_id, status="processing", progress=0, step="Préparation du traitement", startedAt=datetime.now(timezone.utc), error=None)


def update_progress(job_id: str, progress: int, step: str) -> None:
    update_job(job_id, progress=max(0, min(100, progress)), step=step)


def mark_done(job_id: str, image_url: str, thumbnail_url: str) -> None:
    update_job(job_id, status="done", progress=100, step="Carte prête", imageUrl=image_url, thumbnailUrl=thumbnail_url, completedAt=datetime.now(timezone.utc), error=None)


def mark_error(job_id: str, message: str) -> None:
    update_job(job_id, status="error", step="Échec du traitement", error=message[:500], completedAt=datetime.now(timezone.utc))
