"""SQLite persistence for RoadAudit AI inspection and verification evidence."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "roadaudit.db"
ROOT = DB_PATH.parents[1]
UPLOADS_PATH = ROOT / "uploads"
OUTPUTS_PATH = ROOT / "outputs"


def utc_now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    database = sqlite3.connect(DB_PATH, timeout=10)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    database.execute("PRAGMA journal_mode = WAL")
    return database


def initialize_database():
    with connect() as database:
        database.execute("""CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_name TEXT NOT NULL,
            is_video INTEGER NOT NULL CHECK(is_video IN (0,1)),
            model_mode TEXT NOT NULL,
            traffic_level INTEGER NOT NULL CHECK(traffic_level BETWEEN 0 AND 100),
            road_type TEXT NOT NULL,
            defects_json TEXT NOT NULL,
            summary_json TEXT NOT NULL
        )""")
        columns = {row["name"] for row in database.execute("PRAGMA table_info(inspections)")}
        if "source_path" not in columns:
            database.execute("ALTER TABLE inspections ADD COLUMN source_path TEXT")
        if "evidence_fingerprint" not in columns:
            database.execute("ALTER TABLE inspections ADD COLUMN evidence_fingerprint TEXT")
        if "annotated_path" not in columns:
            database.execute("ALTER TABLE inspections ADD COLUMN annotated_path TEXT")
        database.execute("""CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            before_inspection_id INTEGER NOT NULL,
            after_source_name TEXT NOT NULL,
            outcome_json TEXT NOT NULL,
            after_defects_json TEXT NOT NULL,
            after_summary_json TEXT NOT NULL,
            FOREIGN KEY(before_inspection_id) REFERENCES inspections(id) ON DELETE CASCADE
        )""")
        # Older prototype databases may predate the foreign-key constraint.
        # Remove any legacy orphan rows during startup so history and counts agree.
        database.execute(
            "DELETE FROM verifications WHERE before_inspection_id NOT IN (SELECT id FROM inspections)"
        )
        database.execute("CREATE INDEX IF NOT EXISTS idx_inspections_created_at ON inspections(created_at DESC)")
        database.execute("CREATE INDEX IF NOT EXISTS idx_verifications_before ON verifications(before_inspection_id)")


def create_inspection(
    name,
    is_video,
    mode,
    traffic,
    road_type,
    defects,
    summary,
    source_path=None,
    evidence_fingerprint=None,
    annotated_path=None,
):
    with connect() as database:
        cursor = database.execute(
            """INSERT INTO inspections
            (created_at,source_name,is_video,model_mode,traffic_level,road_type,defects_json,summary_json,source_path,evidence_fingerprint,annotated_path)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                utc_now(),
                name,
                int(is_video),
                mode,
                traffic,
                road_type,
                json.dumps(defects),
                json.dumps(summary),
                str(source_path) if source_path else None,
                evidence_fingerprint,
                str(annotated_path) if annotated_path else None,
            ),
        )
        return cursor.lastrowid


def list_inspections(limit=None):
    query = "SELECT id,created_at,source_name,model_mode,road_type,summary_json FROM inspections WHERE model_mode <> 'test' ORDER BY id DESC"
    parameters = ()
    if limit:
        query += " LIMIT ?"
        parameters = (int(limit),)
    with connect() as database:
        rows = database.execute(query, parameters).fetchall()
    records = []
    for row in rows:
        summary = json.loads(row["summary_json"])
        records.append({
            "id": row["id"], "created_at": row["created_at"], "source_name": row["source_name"],
            "model_mode": row["model_mode"], "road_type": row["road_type"],
            "road_health_index": summary["road_health_index"], "unique_defects": summary["unique_defects"],
            "urgent_repairs": summary["urgent_repairs"], "duplicates_removed": summary.get("duplicates_removed", 0),
        })
    return records


def get_inspection(inspection_id):
    with connect() as database:
        row = database.execute("SELECT * FROM inspections WHERE id=?", (inspection_id,)).fetchone()
    if not row: return None
    record = dict(row)
    record["defects"] = json.loads(record.pop("defects_json"))
    record["summary"] = json.loads(record.pop("summary_json"))
    return record


def save_verification(before_id, name, outcome, after_defects, after_summary):
    with connect() as database:
        cursor = database.execute(
            "INSERT INTO verifications (created_at,before_inspection_id,after_source_name,outcome_json,after_defects_json,after_summary_json) VALUES (?,?,?,?,?,?)",
            (utc_now(), before_id, name, json.dumps(outcome), json.dumps(after_defects), json.dumps(after_summary)),
        )
        return cursor.lastrowid


def list_verifications(limit=50):
    with connect() as database:
        rows = database.execute("SELECT v.*, i.source_name AS before_source FROM verifications v JOIN inspections i ON i.id=v.before_inspection_id ORDER BY v.id DESC LIMIT ?", (int(limit),)).fetchall()
    records = []
    for row in rows:
        outcome = json.loads(row["outcome_json"])
        records.append({"id": row["id"], "created_at": row["created_at"], "before_inspection_id": row["before_inspection_id"], "before_source": row["before_source"], "after_source_name": row["after_source_name"], "status": outcome["status"], "health_change": outcome["health_change"]})
    return records


def database_stats():
    with connect() as database:
        inspections = database.execute("SELECT COUNT(*) FROM inspections WHERE model_mode <> 'test'").fetchone()[0]
        verifications = database.execute(
            "SELECT COUNT(*) FROM verifications v JOIN inspections i ON i.id=v.before_inspection_id"
        ).fetchone()[0]
    return {"inspections": inspections, "verifications": verifications}


def delete_inspection(inspection_id):
    """Delete one decision record; linked verification rows cascade safely."""
    with connect() as database:
        # Explicit deletion keeps lifecycle safe even for legacy databases
        # whose verifications table was created without a foreign key.
        database.execute("DELETE FROM verifications WHERE before_inspection_id=?", (inspection_id,))
        cursor = database.execute("DELETE FROM inspections WHERE id=?", (inspection_id,))
        return cursor.rowcount > 0


def database_backup_bytes():
    """Return a consistent, downloadable SQLite snapshot."""
    initialize_database()
    handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    snapshot_path = Path(handle.name)
    handle.close()
    try:
        source = connect()
        destination = sqlite3.connect(snapshot_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        return snapshot_path.read_bytes()
    finally:
        snapshot_path.unlink(missing_ok=True)


def _folder_stats(path):
    files = [item for item in path.glob("*") if item.is_file() and item.name != ".gitkeep"]
    return {"files": len(files), "bytes": sum(item.stat().st_size for item in files)}


def storage_stats():
    """Return bounded operational health metrics for retained evidence."""
    initialize_database()
    return {
        **database_stats(),
        "database_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
        "uploads": _folder_stats(UPLOADS_PATH),
        "outputs": _folder_stats(OUTPUTS_PATH),
    }


def remove_unreferenced_evidence(dry_run=True):
    """Find or remove retained uploads and outputs not linked to an inspection."""
    initialize_database()
    with connect() as database:
        referenced = set()
        for row in database.execute(
            "SELECT source_path, annotated_path FROM inspections"
        ).fetchall():
            referenced.update(
                str(Path(value).resolve())
                for value in row
                if value
            )
    candidates = [
        item
        for item in UPLOADS_PATH.glob("*")
        if item.is_file()
        and item.name != ".gitkeep"
        and str(item.resolve()) not in referenced
    ]
    runtime_output_prefixes = ("annotated_", "demo_annotated_", "preview_")
    candidates.extend(
        item
        for item in OUTPUTS_PATH.glob("*")
        if item.is_file()
        and item.name.startswith(runtime_output_prefixes)
        and str(item.resolve()) not in referenced
    )
    reclaimed = sum(item.stat().st_size for item in candidates)
    if not dry_run:
        for item in candidates:
            item.unlink(missing_ok=True)
    return {"files": len(candidates), "bytes": reclaimed, "removed": not dry_run}
