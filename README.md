# RoadAudit AI

RoadAudit AI is an AI-powered road asset intelligence platform that connects road-damage detection to maintenance decisions, crew routing, and repair accountability.

## What the MVP demonstrates

- Image and multi-frame video inspection through an Ultralytics YOLO adapter
- Resolution-independent, image-based severity estimation
- Type-safe GPS deduplication using haversine DBSCAN clustering
- Explainable repair priority scoring with repeat-observation evidence
- Road Health Index, repair budget estimate, charts, and Folium maps
- CSV, JSON, and self-contained HTML inspection reports
- Priority-aware closed repair routes using NetworkX
- Before/after repair-verification records
- FastAPI JSON services, SQLite persistence, and Streamlit operations dashboard
- Guided demo evidence included under `assets/demo_road.png`
- Light and dark dashboard themes

## Architecture

```text
Streamlit Dashboard
        |
        v
FastAPI JSON API ------------- SQLite Evidence Store
        |
        v
YOLO Adapter -> Severity -> DBSCAN -> Priority Engine
                                      |
                         +------------+-------------+
                         v                          v
                 NetworkX Routing          Repair Verification
```

## Run locally

From `D:\RoadAuditAi`:

```powershell
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\run_app.ps1
```

- Dashboard: `http://localhost:8501`
- FastAPI documentation: `http://127.0.0.1:8000/docs`
- FastAPI health: `http://127.0.0.1:8000/health`

The launcher safely reuses an existing API process or starts one and waits until it is healthy before opening Streamlit.

## Guided demo

Open **Inspect Road** and select **Run guided sample inspection**. This uses a bundled, license-safe road image and the visibly labelled demo adapter when trained weights are unavailable.

## Enable trained YOLO inference

Place the teammate's trained Ultralytics model here:

```text
models/road_damage.pt
```

No code changes are required. Image inference runs immediately; video inference samples up to 24 frames and deduplicates repeated observations.

## Priority methodology

```text
Priority = 45% severity
         + 25% road importance
         + 20% traffic level
         + 10% model confidence
         + capped repeat-observation bonus
```

The dashboard exposes these factors for the highest-ranked repair. Severity is an image-space estimate, not a pothole-depth or engineering measurement.

## Run validation

```powershell
powershell -ExecutionPolicy Bypass -File .\run_checks.ps1
```

The checks compile the application, run unit/API/integration tests, and execute a Streamlit rendering smoke test. GitHub Actions repeats the portable checks on every push and pull request.

## Prototype disclosures

- GPS positions, traffic, road importance, and costs are simulated planning inputs.
- Visual repair verification supports review; it does not replace engineering sign-off.
- The fallback adapter is labelled in the UI and must not be presented as trained-model output.

## Demo video

The generated narrated walkthrough is saved locally at `outputs/RoadAudit_AI_Demo_Video.mp4`. Its editable narration is `docs/demo_narration.txt`, and the renderer is `tools/build_demo_video.py`.

## Project layout

```text
app.py                     Streamlit operations dashboard
backend/api.py             FastAPI upload, history, routing, and verification API
ai/detector.py             Cached YOLO adapter and transparent demo fallback
utils/analytics.py         Severity, priority, Road Health Index, DBSCAN
utils/route_planner.py     NetworkX route approximation
utils/reporting.py         Portable inspection report export
utils/verification.py      Before/after comparison policy
utils/storage.py           SQLite evidence store
assets/demo_road.png       Guided-demo inspection evidence
tests/                     Unit, API, and end-to-end guided-demo tests
docs/                      Demo and completion documentation
```
