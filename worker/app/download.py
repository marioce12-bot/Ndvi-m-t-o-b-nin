"""USGS archive download and extraction."""

from __future__ import annotations

import shutil
import time
import zipfile
from pathlib import Path

import requests


def download_and_extract(url: str, workdir: str | Path, retries: int = 2) -> Path:
    """Download one USGS ZIP and return its extracted GeoTIFF path."""
    destination = Path(workdir)
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / Path(url).name

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with requests.get(url, stream=True, timeout=(20, 120)) as response:
                response.raise_for_status()
                with archive.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            output.write(chunk)
            break
        except (OSError, requests.RequestException) as error:
            last_error = error
            archive.unlink(missing_ok=True)
            if attempt == retries:
                raise RuntimeError(f"Echec du telechargement USGS: {url}") from error
            time.sleep(2**attempt)

    if last_error and not archive.exists():
        raise RuntimeError("Archive USGS absente apres le telechargement") from last_error

    extract_dir = destination / "extracted"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as archive_file:
        members = archive_file.infolist()
        tif_members = [member for member in members if member.filename.lower().endswith((".tif", ".tiff"))]
        if len(tif_members) != 1:
            raise ValueError(f"Archive USGS inattendue: {len(tif_members)} GeoTIFF trouve(s)")
        tif_member = tif_members[0]
        target = (extract_dir / Path(tif_member.filename).name).resolve()
        if target.parent != extract_dir.resolve():
            raise ValueError("Chemin d'extraction ZIP non securise")
        with archive_file.open(tif_member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    return target
