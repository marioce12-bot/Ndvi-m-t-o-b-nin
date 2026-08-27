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


def list_agro_stations(principale: bool | None = None) -> list[dict[str, object]]:
    query = get_client().collection("agroStations")
    if principale is not None:
        query = query.where("principal", "==", principale)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def ensure_principal_stations() -> None:
    stations = {
        "cotonou": ("Cotonou", "Littoral", "Cotonou"),
        "bohicon": ("Bohicon", "Zou", "Bohicon"),
        "save": ("Savè", "Collines", "Savè"),
        "parakou": ("Parakou", "Borgou", "Parakou"),
        "natitingou": ("Natitingou", "Atacora", "Natitingou"),
        "kandi": ("Kandi", "Alibori", "Kandi"),
    }
    client = get_client()
    batch = client.batch()
    for station_id, (name, department, locality) in stations.items():
        reference = client.collection("agroStations").document(station_id)
        if not reference.get().exists:
            batch.set(reference, {"name": name, "department": department, "locality": locality, "principal": True, "etp_station_id": None})
    batch.commit()


def upsert_agro_station(value: dict[str, object]) -> None:
    station_id = str(value.pop("id"))
    get_client().collection("agroStations").document(station_id).set(value, merge=True)


def list_agro_rain(year: int, month: int, decade: int, station_id: str | None = None) -> list[dict[str, object]]:
    query = get_client().collection("agroRainDaily").where("year", "==", year).where("month", "==", month).where("decade", "==", decade)
    if station_id: query = query.where("station_id", "==", station_id)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def upsert_agro_rain(payloads: list[dict[str, object]]) -> None:
    batch = get_client().batch()
    collection = get_client().collection("agroRainDaily")
    for value in payloads:
        doc_id = f"{value['station_id']}-{value['year']}-{value['month']:02d}-{value['decade']}-{value['jour']}"
        batch.set(collection.document(doc_id), value, merge=True)
    batch.commit()


def list_agro_observations(year: int, month: int, decade: int, station_id: str) -> list[dict[str, object]]:
    query = get_client().collection("agroObservations").where("year", "==", year).where("month", "==", month).where("decade", "==", decade).where("station_id", "==", station_id)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def upsert_agro_observations(payloads: list[dict[str, object]]) -> None:
    batch = get_client().batch()
    collection = get_client().collection("agroObservations")
    for value in payloads:
        doc_id = f"{value['station_id']}-{value['year']}-{value['month']:02d}-{value['decade']}-{value['jour']}"
        batch.set(collection.document(doc_id), value, merge=True)
    batch.commit()


def get_agro_ew_etp(year: int, month: int, decade: int) -> list[dict[str, object]]:
    query = get_client().collection("agroEwEtp").where("year", "==", year).where("month", "==", month).where("decade", "==", decade)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def upsert_agro_ew_etp(payloads: list[dict[str, object]]) -> None:
    batch = get_client().batch()
    collection = get_client().collection("agroEwEtp")
    for value in payloads:
        doc_id = f"{value['station_id']}-{value['year']}-{value['month']:02d}-{value['decade']}"
        batch.set(collection.document(doc_id), value, merge=True)
    batch.commit()


def list_users() -> list[tuple[str, str]]:
    """Return registered Firebase users that have an email address."""
    return [(user.uid, user.email) for user in auth.list_users().iterate_all() if user.email]


def save_pentades(product: str, pentades: list[dict[str, object]]) -> None:
    get_client().collection("pentadeCatalog").document(product).set({"pentades": pentades, "updatedAt": _now()})


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
