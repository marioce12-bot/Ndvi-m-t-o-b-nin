"""Firestore job persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache

import firebase_admin
from firebase_admin import auth, credentials, firestore

from .config import get_settings


@lru_cache
def get_client():
    settings = get_settings()
    if not settings.firebase_service_account_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON est absent")
    if not firebase_admin._apps:
        data = json.loads(settings.firebase_service_account_json)
        firebase_admin.initialize_app(credentials.Certificate(data))
    return firestore.client()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_job(job_id: str):
    return get_client().collection("jobs").document(job_id).get()


def list_users() -> list[tuple[str, str]]:
    """Return registered Firebase users that have an email address."""
    return [(user.uid, user.email) for user in auth.list_users().iterate_all() if user.email]


def save_pentades(product: str, pentades: list[dict[str, object]]) -> None:
    get_client().collection("pentadeCatalog").document(product).set({"pentades": pentades, "updatedAt": _now()})


def get_pentades(product: str) -> list[dict[str, object]]:
    snapshot = get_client().collection("pentadeCatalog").document(product).get()
    if not snapshot.exists:
        return []
    value = snapshot.to_dict().get("pentades", [])
    return value if isinstance(value, list) else []


def save_rainfall_import(import_data: dict[str, object]) -> None:
    key = f"{import_data['source']}-{import_data['year']}-{import_data['month']:02d}-{import_data['decade']}"
    get_client().collection("rainfallImports").document(key).set({**import_data, "updatedAt": _now()})


def list_rainfall_imports(source: str | None = None) -> list[dict[str, object]]:
    query = get_client().collection("rainfallImports")
    if source:
        query = query.where("source", "==", source)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def build_rainfall_output() -> list[dict[str, object]]:
    imports = list_rainfall_imports("decades")
    by_station: dict[str, dict[str, object]] = {}
    rainfall_normals = {str(row.get("station", "")).upper(): row for row in get_client().collection("rainfallNormals").document("rainfall").collection("rows").stream() for row in [{**row.to_dict()}]}
    agro_normals = {str(row.get("station", "")).upper(): row for row in get_client().collection("rainfallNormals").document("agro").collection("rows").stream() for row in [{**row.to_dict()}]}
    for item in imports:
        for row in item.get("rows", []):
            station = str(row.get("station", ""))
            if not station:
                continue
            target = by_station.setdefault(station, {"station": station, "department": row.get("department"), "nbRainDays": 0, "nbOver20": 0, "decadeTotal": 0.0, "maxDaily": None, "yearTotal": 0.0, "seasonTotal": 0.0, "waterBalance": None, "normalDecade": None, "normalSeason": None, "decadeDeviation": None, "yearDeviation": None, "seasonDeviation": None, "etp": None})
            target["nbRainDays"] += int(row.get("nbRainDays") or 0)
            target["nbOver20"] += int(row.get("nbOver20") or 0)
            target["decadeTotal"] += float(row.get("decadeTotal") or 0)
            target["yearTotal"] += float(row.get("decadeTotal") or 0)
            month = int(item.get("month") or 0)
            department = str(target.get("department") or "").upper()
            north = any(name in department for name in ("ATACORA", "DONGA", "BORGOU", "ALIBORI"))
            in_season = (4 <= month <= 10) if north else (3 <= month <= 7 or 9 <= month <= 11)
            if in_season: target["seasonTotal"] += float(row.get("decadeTotal") or 0)
            target["yearDeviation"] = target["yearTotal"]
            max_daily = row.get("maxDaily")
            if max_daily is not None and (target["maxDaily"] is None or max_daily > target["maxDaily"]): target["maxDaily"] = max_daily
            code = f"{int(item.get('month', 0)):02d}-{int(item.get('decade', 0))}"
            normal = rainfall_normals.get(station.upper())
            if normal:
                target["normalDecade"] = normal.get("cuma")
                target["normalSeason"] = normal.get("cums")
                target["decadeDeviation"] = target["decadeTotal"] - float(normal.get("cuma") or 0)
                target["seasonDeviation"] = target["seasonTotal"] - float(normal.get("cums") or 0)
            agro = agro_normals.get(station.upper())
            if agro:
                target["etp"] = agro.get("etp") or agro.get("evapPan")
                if target["etp"] is not None: target["waterBalance"] = target["decadeTotal"] - float(target["etp"])
    return list(by_station.values())


def create_rainfall_job(job_id: str, source: str) -> None:
    get_client().collection("rainfallJobs").document(job_id).set({"source": source, "status": "queued", "progress": 0, "error": None, "createdAt": _now(), "completedAt": None})


def update_rainfall_job(job_id: str, **fields: object) -> None:
    get_client().collection("rainfallJobs").document(job_id).update(fields)


def get_rainfall_job(job_id: str):
    return get_client().collection("rainfallJobs").document(job_id).get()


def save_normals(kind: str, rows: list[dict[str, object]]) -> None:
    batch = get_client().batch()
    collection = get_client().collection("rainfallNormals").document(kind).collection("rows")
    for index, row in enumerate(rows):
        batch.set(collection.document(str(index)), row)
    batch.commit()


def find_done_job(product: str, pentade_id: str, owner_id: str):
    query = get_client().collection("jobs").where("product", "==", product).where("pentadeId", "==", pentade_id).where("ownerId", "==", owner_id).where("status", "==", "done").limit(1)
    return next(iter(query.stream()), None)


def create_pending(job_id: str, product: str, pentade_id: str, label: str, email: str, owner_id: str) -> None:
    get_client().collection("jobs").document(job_id).set({
        "product": product, "pentadeId": pentade_id, "label": label, "email": email, "ownerId": owner_id, "status": "pending", "progress": 0, "step": "En attente",
        "imageUrl": None, "thumbnailUrl": None, "error": None, "createdAt": _now(),
        "startedAt": None, "completedAt": None,
    })


def update_job(job_id: str, **fields) -> None:
    get_client().collection("jobs").document(job_id).update(fields)


def mark_processing(job_id: str) -> None:
    update_job(job_id, status="processing", progress=0, step="Préparation du traitement", startedAt=_now(), error=None)


def update_progress(job_id: str, progress: int, step: str) -> None:
    update_job(job_id, progress=max(0, min(100, progress)), step=step)


def mark_done(job_id: str, image_url: str, thumbnail_url: str) -> None:
    update_job(job_id, status="done", progress=100, step="Carte prête", imageUrl=image_url, thumbnailUrl=thumbnail_url, completedAt=_now(), error=None)


def mark_error(job_id: str, message: str) -> None:
    update_job(job_id, status="error", step="Échec du traitement", error=message[:500], completedAt=_now())
