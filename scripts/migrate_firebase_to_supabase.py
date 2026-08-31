"""One-shot migration from Firebase exports to Supabase.

Usage:
  python scripts/migrate_firebase_to_supabase.py firebase-export.json

The JSON must contain collections as top-level keys, with arrays of documents.
It never deletes Firebase data.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from supabase import create_client


def rows(payload: dict, name: str) -> list[dict]:
    values = payload.get(name, [])
    if isinstance(values, dict):
        return [{"id": key, **value} for key, value in values.items()]
    return values


def rename(row: dict, mapping: dict[str, str]) -> dict:
    return {mapping.get(key, key): value for key, value in row.items()}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/migrate_firebase_to_supabase.py firebase-export.json")
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(url, key)

    jobs = [rename(row, {"ownerId": "owner_id", "pentadeId": "pentade_id", "imageUrl": "image_url", "thumbnailUrl": "thumbnail_url", "startedAt": "started_at", "completedAt": "completed_at", "createdAt": "created_at"}) for row in rows(payload, "jobs")]
    stations = rows(payload, "agroStations")
    rain = rows(payload, "agroRainDaily")
    observations = rows(payload, "agroObservations")
    ew_etp = rows(payload, "agroEwEtp")
    catalog = [rename(row, {"updatedAt": "updated_at"}) for row in rows(payload, "pentadeCatalog")]

    for table, values, conflict in (("jobs", jobs, "id"), ("agro_stations", stations, "id"), ("agro_rain_daily", rain, "id"), ("agro_observations", observations, "id"), ("agro_ew_etp", ew_etp, "id"), ("pentade_catalog", catalog, "product")):
        if values:
            response = client.table(table).upsert(values, on_conflict=conflict).execute()
            print(table, len(response.data or values))


if __name__ == "__main__":
    main()
