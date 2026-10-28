"""End-to-end smoke test for the bundled guided-demo evidence."""
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from backend.api import app
from utils.storage import connect, get_inspection


class GuidedDemoIntegrationTest(unittest.TestCase):
    def test_bundled_image_completes_inspection_pipeline(self):
        demo_path = Path(__file__).resolve().parents[1] / "assets" / "demo_road.png"
        self.assertTrue(demo_path.exists())
        client = TestClient(app)
        inspection_id = None
        source_path = None
        annotated_path = None
        try:
            with demo_path.open("rb") as image:
                response = client.post("/api/inspect", files={"file": ("automated-guided-demo.png", image, "image/png")}, data={"traffic_level": 70, "road_type": "Main road", "demo": "true"})
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertEqual(payload["model_mode"], "guided sample (synthetic detections)")
            inspection_id = payload["inspection_id"]
            record = get_inspection(inspection_id)
            source_path = Path(record["source_path"])
            annotated_path = Path(record["annotated_path"])
            self.assertGreaterEqual(len(payload["defects"]), 1)
            self.assertIn("road_health_index", payload["summary"])
            self.assertTrue(annotated_path.exists())
            self.assertTrue(record["evidence_fingerprint"])
        finally:
            if inspection_id:
                with connect() as database:
                    database.execute("DELETE FROM inspections WHERE id=?", (inspection_id,))
            if source_path:
                source_path.unlink(missing_ok=True)
            if annotated_path:
                annotated_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
