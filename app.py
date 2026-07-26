from pathlib import Path
import os
import tempfile

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from ai.detector import MODEL_PATH, inspect_media
from utils.analytics import build_summary, enrich_detections, remove_duplicates
from utils.map_view import build_map, build_route_map
from utils.route_planner import plan_route
from utils.storage import create_inspection, get_inspection, initialize_database, list_inspections, save_verification
from utils.verification import compare_inspections


ROOT = Path(__file__).parent
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)
API_URL = os.getenv("ROAD_AUDIT_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RoadAudit AI", page_icon="RA", layout="wide", initial_sidebar_state="expanded")
initialize_database()


def save_upload(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix.lower(), dir=UPLOADS) as file:
        file.write(uploaded_file.getbuffer())
        return Path(file.name)


def severity_color(severity):
    return {"Critical": "#ef4444", "Severe": "#f97316", "Moderate": "#eab308", "Minor": "#22c55e"}.get(severity, "#64748b")


def run_inspection(uploaded_file, traffic, road_type):
    payload = uploaded_file.getvalue()
    try:
        response = requests.post(
            f"{API_URL}/api/inspect",
            files={"file": (uploaded_file.name, payload, uploaded_file.type or "application/octet-stream")},
            data={"traffic_level": traffic, "road_type": road_type},
            timeout=180,
        )
        response.raise_for_status()
        result = response.json()
        return result["inspection_id"], result["defects"], result["summary"], Path(result["annotated_path"]), result["model_mode"]
    except requests.RequestException:
        path = save_upload(uploaded_file)
        raw, annotated, mode = inspect_media(path)
        defects = remove_duplicates(enrich_detections(raw, traffic, road_type))
        summary = build_summary(defects)
        inspection_id = create_inspection(uploaded_file.name, path.suffix.lower() in {".mp4", ".avi", ".mov"}, mode, traffic, road_type, defects, summary)
        return inspection_id, defects, summary, annotated, f"{mode} (local fallback)"


def latest_inspection():
    records = list_inspections()
    return get_inspection(records[0]["id"]) if records else None


def section_header(eyebrow, title, description):
    st.markdown(
        f"""<div class="section-heading"><div class="eyebrow">{eyebrow}</div>
        <h2>{title}</h2><p>{description}</p></div>""",
        unsafe_allow_html=True,
    )


def metric_cards(summary=None, items=None):
    items = items or [
        ("Road Health Index", f"{summary['road_health_index']}%", summary["health_label"], "cyan"),
        ("Unique Defects", str(summary["unique_defects"]), f"{summary['raw_detections']} raw observations", "blue"),
        ("Urgent Repairs", str(summary["urgent_repairs"]), "Priority score above 80", "red"),
        ("Estimated Budget", f"Rs. {summary['estimated_cost']:,.0f}", "Planning estimate", "green"),
    ]
    columns = st.columns(4)
    for column, (label, value, note, accent) in zip(columns, items):
        with column:
            st.markdown(
                f"""<div class="metric-card {accent}"><div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>""",
                unsafe_allow_html=True,
            )


def empty_state(title, body, number):
    st.markdown(
        f"""<div class="empty-state"><div class="empty-number">{number}</div>
        <div><h3>{title}</h3><p>{body}</p></div></div>""",
        unsafe_allow_html=True,
    )


try:
    api_online = requests.get(f"{API_URL}/health", timeout=1).ok
except requests.RequestException:
    api_online = False
model_ready = MODEL_PATH.exists()
all_records = list_inspections()

st.markdown(
    """
    <style>
    :root {--navy:#071426;--panel:#0c2038;--blue:#2563eb;--cyan:#22d3ee;--ink:#102033;--muted:#66758a;--line:#dbe4ef;--bg:#f3f6fb;}
    .stApp {background:var(--bg);color:var(--ink);font-family:"Segoe UI",Arial,sans-serif;}
    [data-testid="stHeader"] {background:transparent;height:0;}
    [data-testid="stToolbar"] {display:none;}
    .block-container {max-width:1500px;padding:1.45rem 2.2rem 4rem;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#071426 0%,#0b213b 100%);border-right:1px solid #163451;}
    [data-testid="stSidebar"] * {color:#eaf2fb;}
    [data-testid="stSidebar"] .stSelectbox label,[data-testid="stSidebar"] .stSlider label {font-weight:650;color:#c9d8e8;}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {background:#102943;border-color:#264a6b;}
    [data-testid="stSidebar"] hr {border-color:#26435f;}
    .sidebar-brand {padding:.25rem 0 1.4rem;border-bottom:1px solid #26435f;margin-bottom:1.15rem;}
    .brand-mark {display:inline-flex;width:42px;height:42px;align-items:center;justify-content:center;border-radius:12px;background:linear-gradient(135deg,#2563eb,#22d3ee);font-weight:800;color:white;margin-right:10px;}
    .brand-name {font-size:1.22rem;font-weight:750;vertical-align:middle;}
    .sidebar-kicker {color:#7dd3fc!important;text-transform:uppercase;letter-spacing:.12em;font-size:.7rem;font-weight:800;margin:1.2rem 0 .55rem;}
    .workflow-step {display:flex;gap:10px;align-items:center;color:#b9c9d9!important;font-size:.82rem;margin:.52rem 0;}
    .workflow-step span {display:inline-flex;width:24px;height:24px;border-radius:8px;background:#153653;align-items:center;justify-content:center;color:#67e8f9!important;font-weight:750;}
    .hero {position:relative;overflow:hidden;padding:1.65rem 1.8rem;border-radius:22px;background:linear-gradient(120deg,#071426 0%,#0d2b4b 58%,#164e63 100%);color:white;box-shadow:0 15px 40px rgba(15,35,60,.14);margin-bottom:1rem;}
    .hero:after {content:"";position:absolute;width:320px;height:320px;right:-60px;top:-150px;border-radius:50%;background:rgba(34,211,238,.12);border:1px solid rgba(103,232,249,.2);}
    .hero-label {color:#67e8f9;text-transform:uppercase;letter-spacing:.14em;font-size:.72rem;font-weight:800;margin-bottom:.45rem;}
    .hero h1 {font-size:2.2rem;line-height:1.05;margin:0 0 .45rem;letter-spacing:-.035em;color:white;}
    .hero p {max-width:730px;margin:0;color:#c6d5e5;font-size:.98rem;}
    .hero-chips {display:flex;gap:8px;flex-wrap:wrap;margin-top:1rem;}
    .status-chip {display:inline-flex;align-items:center;gap:7px;padding:6px 10px;border-radius:999px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.13);font-size:.75rem;color:#e8f3fc;}
    .status-dot {width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 3px rgba(34,197,94,.15);}
    .status-dot.warn {background:#f59e0b;box-shadow:0 0 0 3px rgba(245,158,11,.15);}
    .overview-strip {display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:.8rem 0 1.25rem;}
    .overview-item {background:white;border:1px solid var(--line);border-radius:14px;padding:.75rem 1rem;box-shadow:0 5px 16px rgba(15,35,60,.035);}
    .overview-item b {display:block;font-size:1.08rem;color:#102033;}.overview-item span {font-size:.75rem;color:#758398;}
    div[data-baseweb="tab-list"] {gap:8px;background:white;border:1px solid var(--line);border-radius:14px;padding:6px;box-shadow:0 5px 16px rgba(15,35,60,.04);}
    button[data-baseweb="tab"] {height:42px;border-radius:9px;padding:0 22px;color:#617187;font-weight:700;}
    button[data-baseweb="tab"][aria-selected="true"] {background:#eaf2ff;color:#1d4ed8;}
    [data-baseweb="tab-highlight"] {display:none;}
    .section-heading {margin:1.55rem 0 1rem;}.section-heading .eyebrow {font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:#2563eb;font-weight:800;}.section-heading h2 {font-size:1.55rem;letter-spacing:-.025em;margin:.22rem 0;color:#102033;}.section-heading p {color:#6c7a8d;margin:0;max-width:800px;font-size:.9rem;}
    [data-testid="stFileUploader"] {background:white;border:1px solid var(--line);border-radius:16px;padding:8px;}
    [data-testid="stFileUploaderDropzone"] {background:#f8fbff;border:1.5px dashed #a8c3e3;border-radius:12px;min-height:145px;}
    .stButton > button[kind="primary"] {border:0;border-radius:10px;background:linear-gradient(100deg,#2563eb,#0ea5e9);font-weight:750;box-shadow:0 8px 18px rgba(37,99,235,.2);min-height:42px;}
    .stButton > button:not([kind="primary"]),.stDownloadButton > button {border-radius:10px;border-color:#b8c9dc;color:#26415f;background:white;font-weight:650;}
    [data-testid="stVerticalBlockBorderWrapper"] {background:white;border-color:var(--line)!important;border-radius:16px!important;box-shadow:0 6px 20px rgba(15,35,60,.035);}
    .metric-card {position:relative;min-height:136px;background:white;border:1px solid var(--line);border-radius:16px;padding:1rem 1.1rem 1rem 1.25rem;overflow:hidden;box-shadow:0 7px 22px rgba(15,35,60,.05);}
    .metric-card:before {content:"";position:absolute;left:0;top:0;width:5px;height:100%;background:#2563eb;}.metric-card.cyan:before{background:#06b6d4}.metric-card.red:before{background:#ef4444}.metric-card.green:before{background:#22c55e}
    .metric-label {font-size:.72rem;color:#728196;text-transform:uppercase;letter-spacing:.06em;font-weight:750;}.metric-value {font-size:1.8rem;color:#102033;font-weight:780;margin:.4rem 0 .15rem;letter-spacing:-.03em;}.metric-note {font-size:.74rem;color:#7b899a;}
    [data-testid="stDataFrame"] {border:1px solid var(--line);border-radius:13px;overflow:hidden;background:white;}
    iframe {border-radius:14px;background:white;}
    .callout {display:flex;gap:14px;align-items:flex-start;background:#eaf4ff;border:1px solid #bdd9f5;border-radius:14px;padding:1rem 1.15rem;margin:.8rem 0 1rem;}.callout .rank {min-width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:#2563eb;color:white;border-radius:10px;font-weight:800;}.callout h4 {margin:0 0 .18rem;color:#15314f}.callout p {margin:0;color:#57708a;font-size:.86rem;}
    .empty-state {display:flex;align-items:center;gap:18px;background:white;border:1px dashed #aec4db;border-radius:16px;padding:1.5rem;margin:1rem 0;}.empty-number {width:48px;height:48px;border-radius:14px;background:#eaf2ff;color:#2563eb;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.15rem;}.empty-state h3{margin:0 0 .2rem;color:#17314d;font-size:1rem}.empty-state p{margin:0;color:#718096;font-size:.86rem}
    .verification-banner {border-radius:15px;padding:1rem 1.2rem;background:#ecfdf5;border:1px solid #a7f3d0;color:#14532d;font-weight:700;margin:.7rem 0 1rem;}
    @media(max-width:900px){.overview-strip{grid-template-columns:1fr}.metric-card{margin-bottom:.5rem}.block-container{padding:1rem}.hero h1{font-size:1.7rem}}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><span class="brand-mark">RA</span><span class="brand-name">RoadAudit AI</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-kicker">Inspection context</div>', unsafe_allow_html=True)
    road_type = st.selectbox("Road importance", ["Hospital / emergency route", "Main road", "Local road"], index=1)
    traffic_level = st.slider("Traffic level", 0, 100, 70, help="Prototype estimate used in the priority score.")
    st.markdown('<div class="sidebar-kicker">System status</div>', unsafe_allow_html=True)
    st.success("FastAPI connected") if api_online else st.warning("Local pipeline active")
    st.success("YOLO weights ready") if model_ready else st.info("Demo inference mode")
    st.markdown('<div class="sidebar-kicker">Decision pipeline</div>', unsafe_allow_html=True)
    st.markdown("""<div class="workflow-step"><span>1</span>Detect visible road damage</div>
    <div class="workflow-step"><span>2</span>Merge duplicate observations</div>
    <div class="workflow-step"><span>3</span>Score repair priority</div>
    <div class="workflow-step"><span>4</span>Optimize crew route</div>
    <div class="workflow-step"><span>5</span>Verify repair evidence</div>""", unsafe_allow_html=True)
    st.divider()
    st.caption("GPS, traffic, cost and road importance are transparent prototype assumptions.")

latest_summary = get_inspection(all_records[0]["id"])["summary"] if all_records else None
api_chip = "API online" if api_online else "Local mode"
model_chip = "YOLO model loaded" if model_ready else "Demo model adapter"
st.markdown(
    f"""<div class="hero"><div class="hero-label">Municipal road intelligence</div>
    <h1>Turn every road survey into a repair decision.</h1>
    <p>Detect visible damage, eliminate duplicate reports, prioritize maintenance, optimize crew routes and verify completed work from one operational dashboard.</p>
    <div class="hero-chips"><span class="status-chip"><i class="status-dot{' warn' if not api_online else ''}"></i>{api_chip}</span>
    <span class="status-chip"><i class="status-dot{' warn' if not model_ready else ''}"></i>{model_chip}</span>
    <span class="status-chip">FastAPI + SQLite</span><span class="status-chip">NetworkX routing</span></div></div>""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""<div class="overview-strip"><div class="overview-item"><b>{len(all_records)}</b><span>Total inspections</span></div>
    <div class="overview-item"><b>{latest_summary['road_health_index'] if latest_summary else '--'}{'%' if latest_summary else ''}</b><span>Latest road health</span></div>
    <div class="overview-item"><b>{latest_summary['urgent_repairs'] if latest_summary else '--'}</b><span>Latest urgent repairs</span></div></div>""",
    unsafe_allow_html=True,
)

inspect_tab, plan_tab, verify_tab, history_tab = st.tabs(["INSPECT ROAD", "MAINTENANCE PLAN", "VERIFY REPAIR", "HISTORY & TRENDS"])

with inspect_tab:
    section_header("Inspection workspace", "Analyze new road evidence", "Upload a road image or short vehicle video. The platform will detect, deduplicate, score and store the resulting defects.")
    upload_column, guidance_column = st.columns([1.55, .75])
    with upload_column:
        upload = st.file_uploader("Drop inspection evidence here", type=["jpg", "jpeg", "png", "mp4", "avi", "mov"], key="inspect", label_visibility="collapsed")
    with guidance_column:
        with st.container(border=True):
            st.markdown("**Good inspection evidence**")
            st.caption("Forward-facing view · visible road surface · minimal motion blur · short clips for fast processing")
            st.markdown(f"**Context:** {road_type}")
            st.caption(f"Traffic estimate: {traffic_level}/100")
    if upload:
        with st.container(border=True):
            st.caption(f"READY FOR INSPECTION  ·  {upload.name}")
            if Path(upload.name).suffix.lower() in {".mp4", ".avi", ".mov"}:
                st.video(upload)
            else:
                st.image(upload, use_container_width=True)
        if st.button("Run AI road inspection", type="primary", use_container_width=True):
            try:
                with st.spinner("Detecting damage, clustering duplicates and calculating repair priorities..."):
                    inspection_id, defects, summary, annotated, mode = run_inspection(upload, traffic_level, road_type)
                st.session_state.update(latest_id=inspection_id, latest_annotated=str(annotated))
                st.success(f"Inspection #{inspection_id} saved successfully · {mode}")
            except Exception as error:
                st.error(f"Inspection could not be completed: {error}")
    record = get_inspection(st.session_state.get("latest_id")) if st.session_state.get("latest_id") else None
    if not record:
        empty_state("No active inspection", "Upload road evidence above to generate an annotated result and maintenance register.", "01")
    else:
        section_header("Inspection result", f"Decision record #{record['id']}", f"Captured from {record['source_name']} using {record['model_mode']}.")
        metric_cards(record["summary"])
        st.write("")
        visual_column, health_column = st.columns([1.4, .8])
        with visual_column:
            with st.container(border=True):
                st.caption("ANNOTATED INSPECTION EVIDENCE")
                annotated_path = Path(st.session_state.get("latest_annotated", "missing"))
                if annotated_path.exists():
                    st.image(str(annotated_path), use_container_width=True)
                else:
                    st.info("Annotated preview is available immediately after running an inspection.")
        with health_column:
            with st.container(border=True):
                st.caption("ROAD HEALTH PROFILE")
                gauge = px.pie(values=[record["summary"]["road_health_index"], 100-record["summary"]["road_health_index"]], names=["Healthy", "Damage burden"], hole=.72, color_discrete_sequence=["#22c55e", "#e5eaf1"])
                gauge.update_traces(textinfo="none", hovertemplate="%{label}: %{value}%<extra></extra>")
                gauge.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=235, paper_bgcolor="rgba(0,0,0,0)", annotations=[dict(text=f"<b>{record['summary']['road_health_index']}%</b><br>Road health", x=.5, y=.5, showarrow=False, font=dict(size=19, color="#102033"))])
                st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})
                st.caption("Image-based condition indicator for maintenance triage; not an engineering pavement rating.")
        if record["defects"]:
            df = pd.DataFrame(record["defects"]).sort_values("priority_score", ascending=False)
            display = df[["id", "damage_type", "confidence", "severity", "priority", "priority_score", "duplicate_count", "latitude", "longitude"]].copy()
            display.columns = ["Defect ID", "Damage type", "Confidence", "Severity", "Priority", "Score", "Observations", "Latitude", "Longitude"]
            display["Confidence"] = display["Confidence"].map(lambda x: f"{x:.0%}")
            display["Score"] = display["Score"].map(lambda x: f"{x:.0f}/100")
            section_header("Maintenance intelligence", "Repair priority register", "Unique defects are ranked by urgency and supported by explainable evidence.")
            st.dataframe(display, use_container_width=True, hide_index=True, column_config={"Severity": st.column_config.TextColumn(width="small"), "Score": st.column_config.TextColumn(width="small")})
            top = record["defects"][0]
            st.markdown(f"""<div class="callout"><div class="rank">1</div><div><h4>{top['id']} is the highest-priority repair</h4>
            <p>Score {top['priority_score']:.0f}/100 · {top['severity']} {top['damage_type'].lower()} · {top['duplicate_count']} observation(s) · {record['road_type']}</p></div></div>""", unsafe_allow_html=True)
            chart_column, map_column = st.columns([.85, 1.35])
            with chart_column:
                with st.container(border=True):
                    st.caption("DEFECT SEVERITY MIX")
                    counts = df["severity"].value_counts().rename_axis("Severity").reset_index(name="Defects")
                    chart = px.bar(counts, x="Defects", y="Severity", orientation="h", color="Severity", color_discrete_map={x: severity_color(x) for x in counts["Severity"]})
                    chart.update_layout(showlegend=False, margin=dict(l=5, r=10, t=10, b=5), height=355, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    chart.update_xaxes(showgrid=True, gridcolor="#e7edf4", title=None); chart.update_yaxes(title=None)
                    st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
            with map_column:
                with st.container(border=True):
                    st.caption("GEOTAGGED DEFECT MAP")
                    st.components.v1.html(build_map(record["defects"])._repr_html_(), height=355)
            st.download_button("Export inspection register", df.to_csv(index=False).encode(), "roadaudit_inspection.csv", "text/csv", use_container_width=True)

with plan_tab:
    section_header("Crew planning", "Build a priority-aware repair route", "Select the crew capacity and depot. NetworkX generates a practical closed route across the highest-value repairs.")
    active = latest_inspection()
    if not active or not active["defects"]:
        empty_state("No defects available for routing", "Complete an inspection first; its unique defects will automatically appear here.", "02")
    else:
        controls, context = st.columns([1.1, .9])
        with controls:
            with st.container(border=True):
                st.caption("CREW AND DEPOT SETTINGS")
                maximum = st.slider("Maximum repairs this shift", 1, min(10, len(active["defects"])), min(5, len(active["defects"])))
                depot_a, depot_b = st.columns(2)
                with depot_a: depot_lat = st.number_input("Depot latitude", value=32.72520, format="%.5f")
                with depot_b: depot_lon = st.number_input("Depot longitude", value=74.85580, format="%.5f")
                if st.button("Generate optimized repair plan", type="primary", use_container_width=True):
                    st.session_state["route"] = plan_route(active["defects"], (depot_lat, depot_lon), maximum)
        with context:
            with st.container(border=True):
                st.caption("ACTIVE INSPECTION")
                st.markdown(f"### Record #{active['id']}")
                st.write(active["source_name"])
                st.caption(f"{len(active['defects'])} unique defects · {active['road_type']}")
                st.progress(min(100, active["summary"]["road_health_index"])/100, text=f"Road health {active['summary']['road_health_index']}%")
        route = st.session_state.get("route")
        if route:
            section_header("Generated route", "Today's maintenance plan", route.get("algorithm", "Route approximation"))
            route_cost = sum({"Minor":2000,"Moderate":7000,"Severe":15000,"Critical":35000}[x["severity"]] for x in route["stops"])
            metric_cards(items=[
                ("Scheduled Repairs", str(len(route["stops"])), f"of {len(active['defects'])} available defects", "blue"),
                ("Route Distance", f"{route['distance_km']:.2f} km", "Closed route from depot", "cyan"),
                ("Priority Coverage", f"{route['priority_coverage']:.0f}%", "Urgency covered this shift", "green"),
                ("Shift Budget", f"Rs. {route_cost:,.0f}", "Planning estimate", "red"),
            ])
            route_df = pd.DataFrame([{"Stop": i+1, "Defect": x["id"], "Damage": x["damage_type"], "Severity": x["severity"], "Priority": f"{x['priority_score']:.0f}/100"} for i, x in enumerate(route["stops"])])
            table_col, route_col = st.columns([.75, 1.35])
            with table_col:
                with st.container(border=True):
                    st.caption("ORDERED REPAIR STOPS")
                    st.dataframe(route_df, use_container_width=True, hide_index=True)
                    st.metric("Total route distance", f"{route['distance_km']:.2f} km")
            with route_col:
                with st.container(border=True):
                    st.caption("OPTIMIZED CREW ROUTE")
                    st.components.v1.html(build_route_map(route)._repr_html_(), height=440)

with verify_tab:
    section_header("Accountability", "Verify completed maintenance", "Compare a saved inspection with new post-repair evidence. The result supports review; it does not replace engineering sign-off.")
    records = list_inspections()
    if not records:
        empty_state("No before-repair evidence", "Save an inspection before starting repair verification.", "03")
    else:
        choices = {f"Record #{x['id']} · {x['source_name']} · {x['created_at']}": x["id"] for x in records}
        before_col, after_col = st.columns(2)
        with before_col:
            with st.container(border=True):
                st.caption("BEFORE-REPAIR RECORD")
                before_label = st.selectbox("Select inspection", list(choices), label_visibility="collapsed")
                selected_before = get_inspection(choices[before_label])
                st.metric("Road health", f"{selected_before['summary']['road_health_index']}%")
                st.caption(f"{len(selected_before['defects'])} visible unique defects · {selected_before['road_type']}")
        with after_col:
            with st.container(border=True):
                st.caption("AFTER-REPAIR EVIDENCE")
                after = st.file_uploader("Upload a matching road image", type=["jpg", "jpeg", "png"], key="after", label_visibility="collapsed")
                st.caption("Use a similar camera position and field of view for the most meaningful comparison.")
        if after and st.button("Compare repair evidence", type="primary", use_container_width=True):
            before = get_inspection(choices[before_label])
            try:
                with st.spinner("Inspecting post-repair evidence and comparing visible risk..."):
                    _, after_defects, after_summary, annotated, mode = run_inspection(after, before["traffic_level"], before["road_type"])
                    outcome = compare_inspections(before["defects"], before["summary"], after_defects, after_summary)
                    verification_id = save_verification(before["id"], after.name, outcome, after_defects, after_summary)
                st.markdown(f'<div class="verification-banner">Verification #{verification_id} · {outcome["status"]}</div>', unsafe_allow_html=True)
                comparison = st.columns(3)
                comparison[0].metric("Before health", f"{before['summary']['road_health_index']}%")
                comparison[1].metric("After health", f"{after_summary['road_health_index']}%", f"{outcome['health_change']:+d} points")
                comparison[2].metric("Visible defects", f"{len(before['defects'])} → {len(after_defects)}")
                st.info(outcome["explanation"])
                with st.container(border=True):
                    st.caption(f"POST-REPAIR ANNOTATED EVIDENCE · {mode}")
                    st.image(str(annotated), use_container_width=True)
            except Exception as error:
                st.error(f"Repair verification could not be completed: {error}")

with history_tab:
    section_header("Evidence register", "Inspection history and trends", "Review persisted inspections, track Road Health Index changes and export the municipal evidence register.")
    records = list_inspections()
    if not records:
        empty_state("No inspection history yet", "Completed inspections will appear here with their health score and defect totals.", "04")
    else:
        history = pd.DataFrame(records)
        history["created_at"] = pd.to_datetime(history["created_at"])
        trend_col, volume_col = st.columns([1.2, .8])
        with trend_col:
            with st.container(border=True):
                st.caption("ROAD HEALTH TREND")
                trend = px.line(history.sort_values("created_at"), x="created_at", y="road_health_index", markers=True)
                trend.update_traces(line_color="#2563eb", line_width=3, marker=dict(size=8, color="#22d3ee"))
                trend.update_layout(margin=dict(l=5,r=10,t=10,b=5),height=300,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
                trend.update_xaxes(title=None,gridcolor="#edf1f6"); trend.update_yaxes(title="Road health %",range=[0,100],gridcolor="#edf1f6")
                st.plotly_chart(trend,use_container_width=True,config={"displayModeBar":False})
        with volume_col:
            with st.container(border=True):
                st.caption("DEFECTS BY INSPECTION")
                volume = px.bar(history.sort_values("created_at"), x="id", y="unique_defects", color_discrete_sequence=["#0ea5e9"])
                volume.update_layout(margin=dict(l=5,r=10,t=10,b=5),height=300,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
                volume.update_xaxes(title="Inspection ID",gridcolor="#edf1f6"); volume.update_yaxes(title="Unique defects",gridcolor="#edf1f6")
                st.plotly_chart(volume,use_container_width=True,config={"displayModeBar":False})
        display_history = history.copy()
        display_history["created_at"] = display_history["created_at"].dt.strftime("%d %b %Y · %H:%M")
        display_history.columns = ["ID","Inspected at","Source","Inference mode","Road type","Road health","Unique defects","Urgent repairs"]
        st.dataframe(display_history, use_container_width=True, hide_index=True)
        st.download_button("Export complete inspection history", history.to_csv(index=False).encode(), "roadaudit_history.csv", "text/csv", use_container_width=True)
