"""SQLite persistence for the hackathon MVP."""
from datetime import datetime
import json
from pathlib import Path
import sqlite3

DB_PATH=Path(__file__).resolve().parents[1]/"database"/"roadaudit.db"
def connect():
    DB_PATH.parent.mkdir(exist_ok=True); db=sqlite3.connect(DB_PATH); db.row_factory=sqlite3.Row; return db
def initialize_database():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS inspections (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, source_name TEXT NOT NULL, is_video INTEGER NOT NULL, model_mode TEXT NOT NULL, traffic_level INTEGER NOT NULL, road_type TEXT NOT NULL, defects_json TEXT NOT NULL, summary_json TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS verifications (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, before_inspection_id INTEGER NOT NULL, after_source_name TEXT NOT NULL, outcome_json TEXT NOT NULL, after_defects_json TEXT NOT NULL, after_summary_json TEXT NOT NULL)")
def create_inspection(name,is_video,mode,traffic,road_type,defects,summary):
    with connect() as db:
        return db.execute("INSERT INTO inspections (created_at,source_name,is_video,model_mode,traffic_level,road_type,defects_json,summary_json) VALUES (?,?,?,?,?,?,?,?)",(datetime.now().isoformat(timespec="seconds"),name,int(is_video),mode,traffic,road_type,json.dumps(defects),json.dumps(summary))).lastrowid
def list_inspections():
    # Ignore internal smoke-test rows should a developer run the module check locally.
    with connect() as db: rows=db.execute("SELECT id,created_at,source_name,model_mode,road_type,summary_json FROM inspections WHERE model_mode <> 'test' ORDER BY id DESC").fetchall()
    records=[]
    for row in rows:
        s=json.loads(row["summary_json"]); records.append({"id":row["id"],"created_at":row["created_at"],"source_name":row["source_name"],"model_mode":row["model_mode"],"road_type":row["road_type"],"road_health_index":s["road_health_index"],"unique_defects":s["unique_defects"],"urgent_repairs":s["urgent_repairs"]})
    return records
def get_inspection(inspection_id):
    with connect() as db: row=db.execute("SELECT * FROM inspections WHERE id=?",(inspection_id,)).fetchone()
    if not row:return None
    record=dict(row); record["defects"]=json.loads(record.pop("defects_json")); record["summary"]=json.loads(record.pop("summary_json")); return record
def save_verification(before_id,name,outcome,after_defects,after_summary):
    with connect() as db:
        return db.execute("INSERT INTO verifications (created_at,before_inspection_id,after_source_name,outcome_json,after_defects_json,after_summary_json) VALUES (?,?,?,?,?,?)",(datetime.now().isoformat(timespec="seconds"),before_id,name,json.dumps(outcome),json.dumps(after_defects),json.dumps(after_summary))).lastrowid
