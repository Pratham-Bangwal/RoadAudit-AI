from pathlib import Path
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

from ai.detector import inspect_media
from utils.analytics import build_summary, enrich_detections, remove_duplicates
from utils.map_view import build_map, build_route_map
from utils.route_planner import plan_route
from utils.storage import create_inspection, get_inspection, initialize_database, list_inspections, save_verification
from utils.verification import compare_inspections

ROOT = Path(__file__).parent
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)
st.set_page_config(page_title="RoadAudit AI", page_icon="RA", layout="wide")
initialize_database()

def save_upload(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix.lower(), dir=UPLOADS) as file:
        file.write(uploaded_file.getbuffer())
        return Path(file.name)

def severity_color(severity):
    return {"Critical":"#dc2626", "Severe":"#f97316", "Moderate":"#eab308", "Minor":"#16a34a"}.get(severity,"#64748b")

def run_inspection(uploaded_file, traffic, road_type):
    path = save_upload(uploaded_file)
    raw, annotated, mode = inspect_media(path)
    defects = remove_duplicates(enrich_detections(raw, traffic, road_type))
    summary = build_summary(defects)
    inspection_id = create_inspection(uploaded_file.name, path.suffix.lower() in {".mp4", ".avi", ".mov"}, mode, traffic, road_type, defects, summary)
    return inspection_id, defects, summary, annotated, mode

def latest_inspection():
    records = list_inspections()
    return get_inspection(records[0]["id"]) if records else None

st.markdown("""<style>.block-container{padding-top:1.5rem}.hero{padding:1.25rem 1.5rem;border-radius:16px;background:linear-gradient(120deg,#0f172a,#1d4ed8);color:#fff;margin-bottom:1rem}[data-testid='stMetric']{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:12px}</style>""", unsafe_allow_html=True)
st.markdown("<div class='hero'><h1 style='margin:0'>RoadAudit AI</h1><p style='margin:5px 0 0'>Road asset intelligence: detection, prioritization, action, and accountability.</p></div>", unsafe_allow_html=True)
with st.sidebar:
    st.header("Prototype controls")
    road_type = st.selectbox("Road importance", ["Hospital / emergency route", "Main road", "Local road"], index=1)
    traffic_level = st.slider("Traffic level (prototype estimate)", 0, 100, 70)
    st.caption("GPS, traffic and road importance are prototype assumptions. Add `models/road_damage.pt` to switch to live YOLO inference.")

inspect_tab, plan_tab, verify_tab, history_tab = st.tabs(["1. Inspect road", "2. Maintenance plan", "3. Verify repair", "4. History"])
with inspect_tab:
    st.subheader("Inspect a road image or short video")
    upload = st.file_uploader("Road image or video", type=["jpg","jpeg","png","mp4","avi","mov"], key="inspect")
    if upload:
        if Path(upload.name).suffix.lower() in {".mp4", ".avi", ".mov"}: st.video(upload)
        else: st.image(upload, caption="Uploaded evidence", use_container_width=True)
        if st.button("Run AI inspection", type="primary", use_container_width=True):
            try:
                with st.spinner("Detecting, deduplicating, and prioritizing road damage..."):
                    inspection_id, defects, summary, annotated, mode = run_inspection(upload, traffic_level, road_type)
                st.session_state.update(latest_id=inspection_id, latest_annotated=str(annotated))
                st.success(f"Inspection #{inspection_id} saved. Inference mode: {mode}.")
            except Exception as error:
                st.error(f"Inspection could not be completed: {error}")
    record = get_inspection(st.session_state.get("latest_id")) if st.session_state.get("latest_id") else None
    if record:
        annotated_col, summary_col = st.columns([1.25,1])
        with annotated_col:
            st.subheader("Annotated inspection")
            if Path(st.session_state.get("latest_annotated", "missing")).exists(): st.image(st.session_state["latest_annotated"], use_container_width=True)
        with summary_col:
            s = record["summary"]
            st.subheader("Decision summary")
            st.metric("Road Health Index", f"{s['road_health_index']}%", s["health_label"])
            st.metric("Unique defects", s["unique_defects"], f"from {s['raw_detections']} raw reports")
            st.metric("Urgent repairs", s["urgent_repairs"])
            st.metric("Estimated budget", f"Rs. {s['estimated_cost']:,.0f}")
        if record["defects"]:
            df = pd.DataFrame(record["defects"]).sort_values("priority_score", ascending=False)
            display = df[["id","damage_type","confidence","severity","priority","priority_score","duplicate_count","latitude","longitude"]].copy()
            display["confidence"] = display["confidence"].map(lambda x:f"{x:.0%}")
            display["priority_score"] = display["priority_score"].map(lambda x:f"{x:.0f}/100")
            st.subheader("Repair priority register"); st.dataframe(display, use_container_width=True, hide_index=True)
            chart_col, map_col = st.columns([1,1.35])
            with chart_col:
                counts=df["severity"].value_counts().rename_axis("severity").reset_index(name="defects")
                chart=px.bar(counts,x="severity",y="defects",color="severity",color_discrete_map={x:severity_color(x) for x in counts["severity"]}); chart.update_layout(showlegend=False,margin=dict(l=10,r=10,t=10,b=10)); st.plotly_chart(chart,use_container_width=True)
            with map_col: st.components.v1.html(build_map(record["defects"])._repr_html_(), height=420)
            top=record["defects"][0]
            st.info(f"Top repair: {top['id']} scores {top['priority_score']:.0f}/100 because it is {top['severity'].lower()}, appears in {top['duplicate_count']} observation(s), and is on a {record['road_type'].lower()}.")
            st.download_button("Download inspection register (CSV)",df.to_csv(index=False).encode(),"roadaudit_inspection.csv","text/csv")
with plan_tab:
    st.subheader("Generate a repair route")
    st.write("The planner schedules the highest-priority defects and applies a nearest-neighbour route approximation.")
    active=latest_inspection()
    if not active or not active["defects"]: st.info("Run an inspection first.")
    else:
        maximum=st.slider("Maximum repairs for this crew",1,min(10,len(active["defects"])),min(5,len(active["defects"])))
        depot_lat=st.number_input("Depot latitude",value=32.72520,format="%.5f"); depot_lon=st.number_input("Depot longitude",value=74.85580,format="%.5f")
        if st.button("Generate repair plan",type="primary"): st.session_state["route"]=plan_route(active["defects"],(depot_lat,depot_lon),maximum)
        route=st.session_state.get("route")
        if route:
            a,b,c=st.columns(3); a.metric("Scheduled repairs",len(route["stops"])); b.metric("Route length",f"{route['distance_km']:.2f} km"); c.metric("Priority coverage",f"{route['priority_coverage']:.0f}%")
            route_df=pd.DataFrame([{ "Stop":i+1,"Defect":x["id"],"Damage":x["damage_type"],"Severity":x["severity"],"Priority":f"{x['priority_score']:.0f}/100"} for i,x in enumerate(route["stops"])])
            st.dataframe(route_df,use_container_width=True,hide_index=True); st.components.v1.html(build_route_map(route)._repr_html_(),height=460)
with verify_tab:
    st.subheader("Verify a completed repair")
    st.write("This is a visual evidence check, not an engineering sign-off.")
    records=list_inspections()
    if not records: st.info("Save an inspection before running repair verification.")
    else:
        choices={f"#{x['id']} - {x['created_at']} - {x['source_name']}":x["id"] for x in records}
        before_label=st.selectbox("Before-repair inspection",list(choices)); after=st.file_uploader("After-repair image",type=["jpg","jpeg","png"],key="after")
        if after and st.button("Run repair verification",type="primary"):
            before=get_inspection(choices[before_label])
            try:
                with st.spinner("Inspecting post-repair evidence..."):
                    _,after_defects,after_summary,annotated,mode=run_inspection(after,before["traffic_level"],before["road_type"])
                    outcome=compare_inspections(before["defects"],before["summary"],after_defects,after_summary)
                    verification_id=save_verification(before["id"],after.name,outcome,after_defects,after_summary)
                st.success(f"Verification #{verification_id}: {outcome['status']}")
                a,b,c=st.columns(3); a.metric("Before health",f"{before['summary']['road_health_index']}%"); b.metric("After health",f"{after_summary['road_health_index']}%",f"{outcome['health_change']:+d} points"); c.metric("Visible defects",f"{len(before['defects'])} to {len(after_defects)}")
                st.write(outcome["explanation"]); st.image(str(annotated),caption=f"Post-repair inspection - {mode}",use_container_width=True)
            except Exception as error:
                st.error(f"Repair verification could not be completed: {error}")
with history_tab:
    st.subheader("Saved inspection records")
    records=list_inspections()
    if not records: st.info("No inspection records saved yet.")
    else:
        history=pd.DataFrame(records); st.dataframe(history[["id","created_at","source_name","model_mode","road_type","road_health_index","unique_defects","urgent_repairs"]],use_container_width=True,hide_index=True)
        st.download_button("Export inspection history (CSV)",history.to_csv(index=False).encode(),"roadaudit_history.csv","text/csv")
