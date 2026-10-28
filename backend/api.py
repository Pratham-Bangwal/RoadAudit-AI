"""FastAPI boundary for RoadAudit AI inspection and decision services."""
from pathlib import Path
from uuid import uuid4
import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from ai.detector import inspect_media
from utils.analytics import build_summary, enrich_detections, remove_duplicates
from utils.evidence import evidence_fingerprint
from utils.route_planner import plan_route
from utils.reporting import build_html_report
from utils.storage import (
    create_inspection,
    database_backup_bytes,
    delete_inspection,
    get_inspection,
    initialize_database,
    list_inspections,
    list_verifications,
    save_verification,
    storage_stats,
)

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"}
ALLOWED_ROAD_TYPES = {"Hospital / emergency route", "Main road", "Local road"}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
LOGGER = logging.getLogger("roadaudit.api")

app = FastAPI(title="RoadAudit AI API", version="1.2.0", description="Inspection, persistence, prioritization, verification, and route-planning services.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"], allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])
initialize_database()


class RouteRequest(BaseModel):
    inspection_id: int
    depot_latitude: float = Field(ge=-90, le=90)
    depot_longitude: float = Field(ge=-180, le=180)
    max_repairs: int = Field(default=5, ge=1, le=100)


class VerificationRequest(BaseModel):
    before_inspection_id: int
    after_source_name: str = Field(min_length=1, max_length=255)
    outcome: dict
    after_defects: list[dict]
    after_summary: dict


@app.get("/health")
def health():
    return {"status": "ok", "service": "RoadAudit AI API", "version": app.version, **storage_stats()}


@app.get("/api/system")
def system_status():
    return {"service": "RoadAudit AI API", "version": app.version, **storage_stats()}


@app.post("/api/inspect")
async def inspect_road(file: UploadFile = File(...), traffic_level: int = Form(default=70, ge=0, le=100), road_type: str = Form(default="Main road"), demo: bool = Form(default=False)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Unsupported image or video format.")
    if road_type not in ALLOWED_ROAD_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported road type.")
    destination = UPLOADS / f"{uuid4().hex}{suffix}"
    total_bytes = 0
    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Upload exceeds the 100 MB prototype limit.")
                output.write(chunk)
        raw, annotated, model_mode = inspect_media(destination, demo=demo)
        defects = remove_duplicates(enrich_detections(raw, traffic_level, road_type))
        summary = build_summary(defects)
        fingerprint = evidence_fingerprint(destination)
        inspection_id = create_inspection(
            file.filename or destination.name,
            suffix in {".mp4", ".avi", ".mov"},
            model_mode,
            traffic_level,
            road_type,
            defects,
            summary,
            source_path=destination,
            evidence_fingerprint=fingerprint,
            annotated_path=annotated,
        )
        return {"inspection_id": inspection_id, "model_mode": model_mode, "annotated_path": str(annotated), "defects": defects, "summary": summary}
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except Exception as error:
        destination.unlink(missing_ok=True)
        LOGGER.exception("Inspection failed")
        raise HTTPException(status_code=500, detail="Inspection could not be completed. Check the evidence format and model configuration.") from error
    finally:
        await file.close()


@app.get("/api/inspections")
def inspections(limit: int = 100):
    return {"inspections": list_inspections(min(max(limit, 1), 500))}


@app.get("/api/inspections/{inspection_id}")
def inspection(inspection_id: int):
    record = get_inspection(inspection_id)
    if not record: raise HTTPException(status_code=404, detail="Inspection not found.")
    return record


@app.get("/api/inspections/{inspection_id}/json")
def inspection_json(inspection_id: int):
    return inspection(inspection_id)


@app.get("/api/inspections/{inspection_id}/report", response_class=HTMLResponse)
def inspection_report(inspection_id: int):
    return build_html_report(inspection(inspection_id))


@app.delete("/api/inspections/{inspection_id}", status_code=204)
def remove_inspection(inspection_id: int):
    if not delete_inspection(inspection_id):
        raise HTTPException(status_code=404, detail="Inspection not found.")
    return Response(status_code=204)


@app.get("/api/backup")
def backup():
    filename = "roadaudit_database_backup.db"
    return Response(
        content=database_backup_bytes(),
        media_type="application/vnd.sqlite3",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/verifications")
def verifications(limit: int = 50):
    return {"verifications": list_verifications(min(max(limit, 1), 500))}


@app.post("/api/verifications")
def create_verification(request: VerificationRequest):
    if not get_inspection(request.before_inspection_id):
        raise HTTPException(status_code=404, detail="Before-repair inspection not found.")
    verification_id = save_verification(request.before_inspection_id, request.after_source_name, request.outcome, request.after_defects, request.after_summary)
    return {"verification_id": verification_id, "status": request.outcome.get("status", "Recorded")}


@app.post("/api/routes")
def route(request: RouteRequest):
    record = get_inspection(request.inspection_id)
    if not record: raise HTTPException(status_code=404, detail="Inspection not found.")
    if not record["defects"]: raise HTTPException(status_code=422, detail="Inspection has no repairable defects.")
    return plan_route(record["defects"], (request.depot_latitude, request.depot_longitude), min(request.max_repairs, len(record["defects"])))
