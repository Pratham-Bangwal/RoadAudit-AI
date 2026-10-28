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
- Before/after repair-verification records with same-road visual consistency checks
- FastAPI JSON services, SQLite persistence, and Streamlit operations dashboard
- Database backup, storage diagnostics, guarded record deletion, and orphan cleanup
- Guided demo evidence included under `assets/demo_road.png`
- Trained YOLO checkpoint and reproducible training/inference scripts from the final handoff
- A separate presentation dashboard with clearly labelled sample data
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
- FastAPI system diagnostics: `http://127.0.0.1:8000/api/system`

The launcher safely reuses an existing API process or starts one and waits until it is healthy before opening Streamlit.

## Guided demo

Open **Inspect Road** and select **Run guided sample inspection**. This uses a bundled road image and visibly labelled synthetic detections, even when trained weights are available. Uploaded images and videos use the trained checkpoint.

## Enable trained YOLO inference

The final handoff's later trained Ultralytics checkpoint is included here:

```text
models/road_damage.pt
```

Image inference uses this checkpoint; video inference samples up to 24 frames and deduplicates repeated observations. The original earlier MVP checkpoint is retained at `model-pipeline/model/best.pt` for comparison. See [model-pipeline/README.md](model-pipeline/README.md) for training and command-line inference.

## Presentation dashboard

The handoff's separate Next.js interface is in `demo-dashboard/`. It displays a fixed sample inspection and is useful for presentation and design reference. It does not call the live FastAPI service or accept live uploads. The Streamlit app above is the operational interface. See [demo-dashboard/README.md](demo-dashboard/README.md) for its run command.

## Consolidation provenance

This repository combines the existing RoadAudit AI application with the distinct model and presentation work from [RoadAudit-AI-Final-Handoff](https://github.com/Pratham-Bangwal/RoadAudit-AI-Final-Handoff), at commit `763aa6a`. Generated inference outputs, repeated videos, training logs, and unused hosting starter files were left out. The original repositories and their commit histories remain available.

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

The current suite covers product logic, evidence fingerprinting, repair mismatch handling, storage metadata, backup integrity, API contracts, and the complete guided-demo inspection flow.

## Prototype disclosures

- GPS positions, traffic, road importance, and costs are simulated planning inputs.
- Visual repair verification supports review; it does not replace engineering sign-off.
- Same-road confidence is a perceptual view-consistency signal, not proof that two captures have identical GPS coordinates.
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
utils/evidence.py          Image/video fingerprints and view similarity
utils/verification.py      Before/after comparison and mismatch policy
utils/storage.py           SQLite evidence store, backup, and lifecycle controls
assets/demo_road.png       Guided-demo inspection evidence
tests/                     Unit, API, and end-to-end guided-demo tests
docs/                      Demo and completion documentation
```
