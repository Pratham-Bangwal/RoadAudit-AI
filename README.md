# RoadAudit AI

RoadAudit AI turns road imagery into an explainable maintenance workflow:

1. Detect visible road damage from image or video evidence.
2. Estimate image-based severity and assign a repair priority.
3. Merge repeated nearby detections using DBSCAN clustering.
4. Generate a crew repair route and show it on a map.
5. Compare before/after evidence to support repair verification.
6. Persist inspections in SQLite and export the registers as CSV.

## Run the MVP

From `D:\RoadAuditAi`:

```powershell
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\run_app.ps1
```

This launches FastAPI on `http://127.0.0.1:8000` and Streamlit on `http://localhost:8501`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Model hand-off

The application runs in a clearly labelled demo fallback until model weights are available. To enable the real model, place the trained Ultralytics weights here:

```text
models/road_damage.pt
```

No application changes are needed. The model should expose road-damage classes; names containing `pothole`, `alligator`, `transverse`, or `longitudinal` are displayed directly.

## Product modules

| Module | What it demonstrates |
| --- | --- |
| Inspect road | Upload, inference, annotated evidence, severity, priorities, Road Health Index |
| Maintenance plan | Priority-aware NetworkX greedy-TSP repair route and map |
| Verify repair | Before/after visual-risk comparison with an explainable status |
| History | SQLite-backed inspection register and CSV export |

## Prototype assumptions

- GPS locations, road importance, and traffic are simulated for the hackathon MVP and disclosed in the UI.
- Severity is an image-space estimate; it does not measure pothole depth or engineering dimensions.
- Repair verification is a visual evidence aid. Critical repairs must be field-verified before sign-off.

## Project layout

```text
app.py                  Streamlit product interface
backend/api.py          FastAPI and explicit JSON API contract
ai/detector.py          YOLO adapter and temporary demo fallback
utils/analytics.py      Severity, priority, RHI, DBSCAN deduplication
utils/route_planner.py  NetworkX repair-route approximation
utils/verification.py   Before/after comparison policy
utils/storage.py        SQLite persistence
database/               Created automatically on first run
docs/DEMO_SCRIPT.md     Suggested 90-second product demo
```
