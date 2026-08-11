"""Firestore job persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore

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


def find_done_job(product: str, pentade_id: str):
    query = get_client().collection("jobs").where("product", "==", product).where("pentadeId", "==", pentade_id).where("status", "==", "done").limit(1)
    return next(iter(query.stream()), None)


def create_pending(job_id: str, product: str, pentade_id: str, label: str) -> None:
    get_client().collection("jobs").document(job_id).set({
        "product": product, "pentadeId": pentade_id, "label": label, "status": "pending",
        "imageUrl": None, "thumbnailUrl": None, "error": None, "createdAt": _now(),
        "startedAt": None, "completedAt": None,
    })


def update_job(job_id: str, **fields) -> None:
    get_client().collection("jobs").document(job_id).update(fields)


def mark_processing(job_id: str) -> None:
    update_job(job_id, status="processing", startedAt=_now(), error=None)


def mark_done(job_id: str, image_url: str, thumbnail_url: str) -> None:
    update_job(job_id, status="done", imageUrl=image_url, thumbnailUrl=thumbnail_url, completedAt=_now(), error=None)


def mark_error(job_id: str, message: str) -> None:
    update_job(job_id, status="error", error=message[:500], completedAt=_now())
