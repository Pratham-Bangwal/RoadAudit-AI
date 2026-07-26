# RoadAudit AI — 90-second product demo

## Before recording

1. Run `streamlit run app.py` from `D:\RoadAuditAi`.
2. Use a clear road image or a short dashcam clip. If the model file is not yet available, say **"demo fallback mode"** once; do not imply those detections are a trained-model result.
3. Keep the browser at 100% zoom and use the same sample evidence for every recording take.

## Talk track and clicks

### 0–12 seconds — problem and product

Say: “RoadAudit AI turns a road inspection from a complaint into an accountable maintenance decision. It detects visible road damage, ranks what needs attention, and helps the team plan and verify the repair.”

Show: the **Inspect road** tab and the upload control.

### 12–35 seconds — inspection intelligence

Say: “We upload road imagery from an existing vehicle camera. The pipeline detects damage, estimates image-based severity, and merges repeated nearby observations so the same pothole is not reported across multiple video frames.”

Click: **Run AI inspection**. Show the annotated evidence, Road Health Index, and repair-priority register.

### 35–52 seconds — explainability

Say: “Every defect receives an explainable priority score based on severity, confidence, road importance, and traffic. The dashboard shows the reason the top repair is first, together with a geotagged map and the estimated budget.”

Show: the priority register, map, and top-repair note.

### 52–70 seconds — action

Say: “The maintenance plan converts the ranked defects into a practical crew route. We select the number of repairs the crew can handle, then generate a priority-aware route from the depot.”

Click: **Maintenance plan**, then **Generate repair plan**. Show route length, priority coverage, stops, and map.

### 70–85 seconds — accountability

Say: “After work is reported complete, a new image can be compared with the prior inspection. RoadAudit AI reports whether the repair is likely complete, partially repaired, or requires manual review.”

Show: **Verify repair**. If time is short, do not run a second upload; point to the fields and state the output.

### 85–90 seconds — close

Say: “RoadAudit AI takes road maintenance from detection to decision, action, and accountability.”

Show: the RoadAudit AI header.

## Judge questions you can answer

**Is the GPS real?**  
“For the MVP, coordinates are simulated and labelled as such. In production, they would come from the vehicle phone or camera GPS stream.”

**Can one camera measure pothole depth?**  
“No. Our severity is image-based and helps triage. Field inspection remains the engineering authority.”

**Why not just detect potholes?**  
“Detection alone creates a list. Our workflow deduplicates it, ranks it, routes a crew, and records before/after evidence.”
