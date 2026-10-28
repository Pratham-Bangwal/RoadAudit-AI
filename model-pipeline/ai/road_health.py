"""Road Health Index calculation for detection payloads."""

from __future__ import annotations

from typing import Any


def compute_road_health_index(detections: list[dict[str, Any]]) -> float:
    """Return a 0-100 health score, where 100 represents no detected damage.

    Each detection contributes a severity-weighted penalty. This MVP formula is
    intended for prioritisation only and requires calibration with road surveys.
    """
    if not detections:
        return 100.0

    total_penalty = sum(float(detection.get("severity", {}).get("score", 0.0)) * 15.0 for detection in detections)
    return round(max(0.0, 100.0 - total_penalty), 2)
