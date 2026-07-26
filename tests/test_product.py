import unittest

from utils.analytics import build_summary, enrich_detections, remove_duplicates, severity_from_bbox
from utils.route_planner import plan_route
from utils.verification import compare_inspections


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

    def test_priority_and_deduplication(self):
        enriched = enrich_detections(self.raw, 80, "Hospital / emergency route")
        unique = remove_duplicates(enriched)
        self.assertLessEqual(len(unique), len(enriched))
        self.assertTrue(all(0 <= item["priority_score"] <= 100 for item in unique))
        self.assertEqual(sum(item["duplicate_count"] for item in unique), len(enriched))

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


if __name__ == "__main__":
    unittest.main()
