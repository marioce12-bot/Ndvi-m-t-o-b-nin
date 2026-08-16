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
