"""FastAPI boundary for RoadAudit AI's inspection and decision services."""
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ai.detector import inspect_media
from utils.analytics import build_summary, enrich_detections, remove_duplicates
from utils.route_planner import plan_route
from utils.storage import create_inspection, get_inspection, initialize_database, list_inspections

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"}

app = FastAPI(title="RoadAudit AI API", version="1.0.0", description="Inspection, persistence, prioritization, and route-planning services.")
initialize_database()


class RouteRequest(BaseModel):
    inspection_id: int
    depot_latitude: float = Field(ge=-90, le=90)
    depot_longitude: float = Field(ge=-180, le=180)
    max_repairs: int = Field(default=5, ge=1, le=100)


@app.get("/health")
def health():
    return {"status": "ok", "service": "RoadAudit AI API", "version": app.version}


@app.post("/api/inspect")
async def inspect_road(
    file: UploadFile = File(...),
    traffic_level: int = Form(default=70, ge=0, le=100),
    road_type: str = Form(default="Main road"),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Unsupported image or video format.")
    destination = UPLOADS / f"{uuid4().hex}{suffix}"
    with destination.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    try:
        raw, annotated, model_mode = inspect_media(destination)
        defects = remove_duplicates(enrich_detections(raw, traffic_level, road_type))
        summary = build_summary(defects)
        inspection_id = create_inspection(file.filename or destination.name, suffix in {".mp4", ".avi", ".mov"}, model_mode, traffic_level, road_type, defects, summary)
        return {"inspection_id": inspection_id, "model_mode": model_mode, "annotated_path": str(annotated), "defects": defects, "summary": summary}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Inspection failed: {error}") from error


@app.get("/api/inspections")
def inspections():
    return {"inspections": list_inspections()}


@app.get("/api/inspections/{inspection_id}")
def inspection(inspection_id: int):
    record = get_inspection(inspection_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found.")
    return record


@app.get("/api/inspections/{inspection_id}/json")
def inspection_json(inspection_id: int):
    """Explicit JSON-storage export contract for integrations."""
    return inspection(inspection_id)


@app.post("/api/routes")
def route(request: RouteRequest):
    record = get_inspection(request.inspection_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found.")
    if not record["defects"]:
        raise HTTPException(status_code=422, detail="Inspection has no repairable defects.")
    return plan_route(record["defects"], (request.depot_latitude, request.depot_longitude), min(request.max_repairs, len(record["defects"])))
