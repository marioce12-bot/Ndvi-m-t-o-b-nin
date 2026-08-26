from __future__ import annotations

import hmac
import logging
import shutil
import tempfile
import threading
import uuid
import time
from fastapi.responses import StreamingResponse
from io import BytesIO
import openpyxl
from fastapi import File, UploadFile
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
from .rainfall import compute_resa_row, parse_agro_normals_xls, parse_agro_xls, parse_decades_xls, parse_decades_xlsx, parse_rainfall_normals_xls

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Plateforme NDVI Benin Worker", version="1.0.0")
_cron_lock = threading.Lock()


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


@app.post("/cron/run", status_code=202, dependencies=[Depends(require_api_key)])
def run_cron(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Start one automatic cycle from an external scheduler such as GitHub Actions."""
    from .cron import run

    if not _cron_lock.acquire(blocking=False):
        return {"status": "already_running"}

    def execute() -> None:
        try:
            run()
        finally:
            _cron_lock.release()

    background_tasks.add_task(execute)
    return {"status": "accepted"}


@app.post("/rainfall/import", dependencies=[Depends(require_api_key)])
async def import_rainfall(background_tasks: BackgroundTasks, source: str, year: int | None = None, month: int | None = None, decade: int | None = None, file: UploadFile = File(...)) -> dict[str, object]:
    if source not in {"decades", "agro"}:
        raise HTTPException(status_code=400, detail="Source supportée: decades ou agro")
    content = await file.read()
    job_id = f"rainfall-{uuid.uuid4().hex}"
    db.create_rainfall_job(job_id, source)

    def process_import() -> None:
        started = time.monotonic()
        try:
            db.update_rainfall_job(job_id, status="processing", progress=10)
            parse_started = time.monotonic()
            metadata = (year, month, decade) if source == "decades" and year and month and decade else None
            parsed = (parse_decades_xlsx(content, metadata) if file.filename and file.filename.lower().endswith(".xlsx") else parse_decades_xls(content)) if source == "decades" else parse_agro_xls(content)
            logger.info("Rainfall import job=%s phase=parse duration_s=%.2f rows=%s", job_id, time.monotonic() - parse_started, len(parsed.rows))
            rows = [compute_resa_row(row) for row in parsed.rows] if source == "decades" else parsed.rows
            payload = {"year": parsed.year, "month": parsed.month, "decade": parsed.decade, "source": parsed.source, "rows": rows}
            db.update_rainfall_job(job_id, progress=80)
            save_started = time.monotonic()
            db.save_rainfall_import(payload)
            logger.info("Rainfall import job=%s phase=firestore duration_s=%.2f", job_id, time.monotonic() - save_started)
            db.update_rainfall_job(job_id, status="done", progress=100, result={"year": parsed.year, "month": parsed.month, "decade": parsed.decade, "rows": len(rows)}, completedAt=db._now())
            logger.info("Rainfall import job=%s status=done total_duration_s=%.2f", job_id, time.monotonic() - started)
        except Exception as error:
            logger.exception("Rainfall import failed")
            db.update_rainfall_job(job_id, status="error", error=str(error)[:500], completedAt=db._now())
            logger.info("Rainfall import job=%s status=error total_duration_s=%.2f", job_id, time.monotonic() - started)

    background_tasks.add_task(process_import)
    return {"status": "accepted", "jobId": job_id}


@app.get("/rainfall/import-jobs/{job_id}", dependencies=[Depends(require_api_key)])
def rainfall_import_job(job_id: str) -> dict[str, object]:
    snapshot = db.get_rainfall_job(job_id)
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="Import introuvable")
    return {"id": snapshot.id, **snapshot.to_dict()}


async def _legacy_import_rainfall(source: str, year: int | None, month: int | None, decade: int | None, file: UploadFile) -> dict[str, object]:
    content = await file.read()
    try:
        metadata = (year, month, decade) if source == "decades" and year and month and decade else None
        parsed = (parse_decades_xlsx(content, metadata) if file.filename and file.filename.lower().endswith(".xlsx") else parse_decades_xls(content)) if source == "decades" else parse_agro_xls(content)
        rows = [compute_resa_row(row) for row in parsed.rows] if source == "decades" else parsed.rows
        payload = {"year": parsed.year, "month": parsed.month, "decade": parsed.decade, "source": parsed.source, "rows": rows}
        db.save_rainfall_import(payload)
        return {"status": "imported", "year": parsed.year, "month": parsed.month, "decade": parsed.decade, "rows": len(rows)}
    except Exception as error:
        logger.exception("Rainfall import failed")
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/rainfall/imports", dependencies=[Depends(require_api_key)])
def rainfall_imports(source: str | None = None) -> dict[str, object]:
    try:
        return {"imports": db.list_rainfall_imports(source)}
    except Exception as error:
        logger.exception("Rainfall imports listing failed")
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/rainfall/output", dependencies=[Depends(require_api_key)])
def rainfall_output() -> dict[str, object]:
    return {"rows": db.build_rainfall_output()}


@app.get("/rainfall/output.xlsx", dependencies=[Depends(require_api_key)])
def rainfall_output_xlsx() -> StreamingResponse:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "RESA-01"
    headers = ["Poste", "Département", "NbJP ≥1 mm", "NbJP >20 mm", "Cumul décadaire", "Normale décade", "Écart décade", "Max journalier", "Cumul année", "Écart année", "Cumul saison", "Normale saison", "Écart saison", "ETP", "Bilan hydrique"]
    sheet.append(headers)
    for row in db.build_rainfall_output(): sheet.append([row.get(key) for key in ["station", "department", "nbRainDays", "nbOver20", "decadeTotal", "normalDecade", "decadeDeviation", "maxDaily", "yearTotal", "yearDeviation", "seasonTotal", "normalSeason", "seasonDeviation", "etp", "waterBalance"]])
    stream = BytesIO(); workbook.save(stream); stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=RESA-01.xlsx"})


@app.post("/rainfall/normals/initialize", dependencies=[Depends(require_api_key)])
def initialize_normals() -> dict[str, int]:
    settings = get_settings()
    if not settings.rainfall_normals_rain_path or not settings.rainfall_normals_agro_path:
        raise HTTPException(status_code=503, detail="Chemins des deux feuilles Normales non configurés")
    rain_rows = parse_rainfall_normals_xls(Path(settings.rainfall_normals_rain_path).read_bytes())
    agro_rows = parse_agro_normals_xls(Path(settings.rainfall_normals_agro_path).read_bytes())
    if not rain_rows or not agro_rows:
        raise HTTPException(status_code=422, detail="Une feuille Normales est vide ou illisible")
    db.save_normals("rainfall", rain_rows)
    db.save_normals("agro", agro_rows)
    return {"rainfallRows": len(rain_rows), "agroRows": len(agro_rows)}


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
