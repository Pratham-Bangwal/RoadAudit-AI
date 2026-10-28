"""Heuristic severity estimation for road-damage detections."""

from __future__ import annotations

from typing import Any


CLASS_BASE_SEVERITY = {
    "Longitudinal_Crack": 0.35,
    "Transverse_Crack": 0.40,
    "Alligator_Crack": 0.60,
    "Pothole": 0.55,
}


def assess_severity(
    class_name: str,
    bbox_xyxy: list[float],
    image_shape: tuple[int, int],
    confidence: float,
) -> dict[str, Any]:
    """Estimate severity from damage type, visible area, and confidence.

    This is an MVP heuristic, not a calibrated engineering assessment. Scores range
    from 0 (minimal) to 1 (severe) and must be validated against field inspections.
    """
    image_height, image_width = image_shape
    if image_height <= 0 or image_width <= 0:
        raise ValueError("image dimensions must be positive")
    if len(bbox_xyxy) != 4:
        raise ValueError("bbox_xyxy must contain four coordinates")

    x1, y1, x2, y2 = bbox_xyxy
    box_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_ratio = min(box_area / (image_width * image_height), 1.0)
    base_score = CLASS_BASE_SEVERITY.get(class_name, 0.40)

    score = min(1.0, (base_score * 0.55) + (min(area_ratio / 0.08, 1.0) * 0.35) + (confidence * 0.10))
    level = (
        "Minor"
        if score < 0.25
        else "Moderate"
        if score < 0.50
        else "Severe"
        if score < 0.75
        else "Critical"
    )

    return {
        "level": level,
        "score": round(score, 4),
        "area_ratio": round(area_ratio, 6),
        "method": "mvp_heuristic",
    }
