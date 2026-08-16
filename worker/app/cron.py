"""Native Render cron entry point for automatic pentade generation."""

from __future__ import annotations

import logging
import time
from datetime import date

from . import db
from .config import get_settings
from .main import GenerateRequest, _run_pipeline
from .pentades import list_available, pentade_for_date, pentade_label

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _sync_catalog(product: str, attempts: int, delay_hours: int) -> list[dict[str, object]] | None:
    """Refresh one catalog atomically; never replace a valid catalog with empty data."""
    last_error = "Catalogue FEWS NET vide"
    for attempt in range(1, max(1, attempts) + 1):
        try:
            catalog = list_available(product)
            if not catalog:
                raise RuntimeError("FEWS NET a renvoye un catalogue vide")
            existing = db.get_pentades(product)
            if existing and len(catalog) < len(existing):
                raise RuntimeError(f"Reponse FEWS NET incomplete ({len(catalog)} < {len(existing)} pentades); catalogue conserve")
            db.save_pentades(product, catalog)
            logger.info("Catalogue %s synchronise: %s pentades", product, len(catalog))
            return catalog
        except Exception as error:
            last_error = str(error)
            logger.warning("Catalogue %s, tentative %s/%s echouee: %s", product, attempt, attempts, error)
        if attempt < attempts:
            time.sleep(max(1, delay_hours) * 3600)
    logger.error("Catalogue %s conserve sans modification: %s", product, last_error)
    return None


def run() -> int:
    settings = get_settings()
    attempts = max(1, settings.cron_retry_attempts)
    primary_catalog = _sync_catalog(settings.cron_product, attempts, settings.cron_retry_delay_hours)
    other_product = "anomaly" if settings.cron_product == "ndvi" else "ndvi"
    _sync_catalog(other_product, attempts, settings.cron_retry_delay_hours)

    target = pentade_for_date(date.today(), settings.cron_safety_delay_days)
    if target is None:
        logger.info("Aucune pentade eligible aujourd'hui")
        return 0
    year = date.today().year
    pentade_id = f"{year}-P{target:02d}"
    label = pentade_label(year, target)
    available = next((item for item in (primary_catalog or []) if item["id"] == pentade_id), None)
    if not available:
        logger.error("Pentade %s indisponible; catalogue conserve", pentade_id)
        return 1
    failures = 0
    for owner_id, email in db.list_users():
        request = GenerateRequest(jobId=f"auto-{settings.cron_product}-{pentade_id}-{owner_id}", pentadeId=pentade_id, product=settings.cron_product, email=email, ownerId=owner_id, force=True)
        last_error = "Echec inconnu"
        for attempt in range(1, max(1, settings.cron_retry_attempts) + 1):
            try:
                db.create_pending(request.jobId, request.product, request.pentadeId, label, request.email, request.ownerId)
                if _run_pipeline(request, label, str(available["url"]), notify_failure=attempt == settings.cron_retry_attempts):
                    break
            except Exception as error:
                last_error = str(error)
                logger.warning("Utilisateur %s, tentative %s/%s echouee: %s", owner_id, attempt, settings.cron_retry_attempts, error)
            if attempt < settings.cron_retry_attempts:
                time.sleep(max(1, settings.cron_retry_delay_hours) * 3600)
        else:
            failures += 1
            logger.error("Echec final pour %s: %s", email, last_error)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
