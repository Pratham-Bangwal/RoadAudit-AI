import unittest
import io
from pathlib import Path
import tempfile

import cv2
import numpy as np

from utils.analytics import build_summary, enrich_detections, remove_duplicates, severity_from_bbox
from utils.evidence import evidence_fingerprint, fingerprint_similarity
from utils.route_planner import plan_route
from utils.verification import compare_inspections
from utils.reporting import build_html_report
from utils.storage import create_inspection, database_backup_bytes, delete_inspection, get_inspection
from backend.api import app
from fastapi.testclient import TestClient


class ProductLogicTests(unittest.TestCase):
    def setUp(self):
        self.raw = [
            {"damage_type": "Pothole", "confidence": .92, "bbox": [0, 0, 300, 300], "frame": 0},
            {"damage_type": "Pothole", "confidence": .88, "bbox": [0, 0, 300, 300], "frame": 15},
        ]

    def test_severity_thresholds(self):
        self.assertEqual(severity_from_bbox([0, 0, 20, 20]), "Minor")
        self.assertEqual(severity_from_bbox([0, 0, 150, 100]), "Moderate")
        self.assertEqual(severity_from_bbox([0, 0, 200, 200]), "Severe")
        self.assertEqual(severity_from_bbox([0, 0, 300, 300]), "Critical")

    def test_normalized_severity_is_resolution_independent(self):
        low_resolution = severity_from_bbox([100, 100, 300, 300], 1000, 1000, "Pothole")
        high_resolution = severity_from_bbox([200, 200, 600, 600], 2000, 2000, "Pothole")
        self.assertEqual(low_resolution, high_resolution)

    def test_priority_and_deduplication(self):
        enriched = enrich_detections(self.raw, 80, "Hospital / emergency route")
        unique = remove_duplicates(enriched)
        self.assertLessEqual(len(unique), len(enriched))
        self.assertTrue(all(0 <= item["priority_score"] <= 100 for item in unique))
        self.assertEqual(sum(item["duplicate_count"] for item in unique), len(enriched))
        self.assertGreaterEqual(unique[0]["priority_factors"]["frequency_bonus"], 0)

    def test_different_damage_types_are_never_merged(self):
        common = {"confidence": .9, "bbox": [0, 0, 100, 100], "frame": 0, "severity": "Moderate", "priority_score": 60, "priority": "High", "latitude": 32.7, "longitude": 74.8}
        detections = [{**common, "id": "A", "damage_type": "Pothole"}, {**common, "id": "B", "damage_type": "Road crack"}]
        unique = remove_duplicates(detections)
        self.assertEqual(len(unique), 2)

    def test_summary_is_bounded(self):
        defects = remove_duplicates(enrich_detections(self.raw, 70, "Main road"))
        summary = build_summary(defects)
        self.assertGreaterEqual(summary["road_health_index"], 0)
        self.assertLessEqual(summary["road_health_index"], 100)
        self.assertGreaterEqual(summary["estimated_cost"], 0)

    def test_route_returns_to_depot(self):
        defects = remove_duplicates(enrich_detections(self.raw, 70, "Main road"))
        depot = (32.7252, 74.8558)
        route = plan_route(defects, depot, 1)
        self.assertEqual(route["points"][0], depot)
        self.assertEqual(route["points"][-1], depot)
        self.assertGreaterEqual(route["distance_km"], 0)

    def test_repair_verification_states(self):
        before = remove_duplicates(enrich_detections(self.raw, 70, "Main road"))
        before_summary = build_summary(before)
        after_summary = build_summary([])
        result = compare_inspections(before, before_summary, [], after_summary)
        self.assertEqual(result["status"], "Repair likely completed")

    def test_repair_verification_rejects_mismatched_evidence(self):
        before = remove_duplicates(enrich_detections(self.raw, 70, "Main road"))
        before_summary = build_summary(before)
        result = compare_inspections(before, before_summary, [], build_summary([]), evidence_similarity=.1)
        self.assertEqual(result["status"], "Evidence mismatch / manual review")
        self.assertEqual(result["evidence_similarity"], .1)

    def test_perceptual_evidence_fingerprint(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "first.png"
            copy = Path(folder) / "copy.png"
            different = Path(folder) / "different.png"
            horizontal = np.tile(np.arange(256, dtype=np.uint8), (256, 1))
            vertical = horizontal.T
            cv2.imwrite(str(first), horizontal)
            cv2.imwrite(str(copy), horizontal)
            cv2.imwrite(str(different), vertical)
            first_hash = evidence_fingerprint(first)
            self.assertEqual(fingerprint_similarity(first_hash, evidence_fingerprint(copy)), 1.0)
            self.assertLess(fingerprint_similarity(first_hash, evidence_fingerprint(different)), .8)

    def test_storage_preserves_evidence_metadata_and_backup(self):
        inspection_id = create_inspection(
            "metadata-test.png",
            False,
            "test",
            70,
            "Main road",
            [],
            build_summary([]),
            source_path="uploads/metadata-test.png",
            evidence_fingerprint="00",
            annotated_path="outputs/metadata-test.png",
        )
        try:
            record = get_inspection(inspection_id)
            self.assertEqual(record["evidence_fingerprint"], "00")
            self.assertTrue(record["source_path"].endswith("metadata-test.png"))
            self.assertGreater(len(database_backup_bytes()), 100)
        finally:
            self.assertTrue(delete_inspection(inspection_id))

    def test_fastapi_health_and_json_contract(self):
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertIn("uploads", response.json())
        system = client.get("/api/system")
        self.assertEqual(system.status_code, 200)
        self.assertIn("database_bytes", system.json())
        backup = client.get("/api/backup")
        self.assertEqual(backup.status_code, 200)
        self.assertGreater(len(backup.content), 100)

    def test_fastapi_rejects_invalid_uploads_and_context(self):
        client = TestClient(app)
        unsupported = client.post("/api/inspect", files={"file": ("road.txt", io.BytesIO(b"test"), "text/plain")})
        self.assertEqual(unsupported.status_code, 415)
        bad_context = client.post("/api/inspect", files={"file": ("road.jpg", io.BytesIO(b"not-an-image"), "image/jpeg")}, data={"road_type": "Unknown"})
        self.assertEqual(bad_context.status_code, 422)

    def test_fastapi_route_and_verification_require_valid_inspection(self):
        client = TestClient(app)
        missing_route = client.post("/api/routes", json={"inspection_id": 999999, "depot_latitude": 32.7, "depot_longitude": 74.8, "max_repairs": 3})
        self.assertEqual(missing_route.status_code, 404)
        missing_verification = client.post("/api/verifications", json={"before_inspection_id": 999999, "after_source_name": "after.jpg", "outcome": {"status": "test"}, "after_defects": [], "after_summary": {}})
        self.assertEqual(missing_verification.status_code, 404)
        missing_delete = client.delete("/api/inspections/999999")
        self.assertEqual(missing_delete.status_code, 404)

    def test_html_report_escapes_untrusted_source_names(self):
        record = {"id": 1, "source_name": "<script>alert(1)</script>.jpg", "created_at": "2026-01-01", "summary": {"road_health_index": 90, "health_label": "Excellent", "unique_defects": 0, "raw_detections": 0, "urgent_repairs": 0, "estimated_cost": 0}, "defects": []}
        report = build_html_report(record)
        self.assertNotIn("<script>alert", report)
        self.assertIn("&lt;script&gt;", report)


if __name__ == "__main__":
    unittest.main()
