"""Backfill existing agro station coordinates without inserting stations."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from supabase import create_client

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    source = Path(__file__).parents[1] / "data" / "station_coordinates_prefill.json"
    entries = json.loads(source.read_text(encoding="utf-8"))
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    updated = 0
    missing = 0
    for station_id, values in entries.items():
        existing = client.table("agro_stations").select("id").eq("id", station_id).maybe_single().execute().data
        if not existing:
            logger.warning("Station absente, aucune insertion: %s (%s)", station_id, values.get("name"))
            missing += 1
            continue
        client.table("agro_stations").update({"longitude": values.get("longitude"), "latitude": values.get("latitude")}).eq("id", station_id).execute()
        updated += 1
    logger.info("Backfill terminé: %s mises à jour, %s stations absentes", updated, missing)


if __name__ == "__main__":
    main()
