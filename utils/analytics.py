"""Road-damage severity, prioritization, deduplication, and summary metrics."""
from collections import defaultdict
import math
import random

import numpy as np
from sklearn.cluster import DBSCAN

SEVERITY_POINTS = {"Minor": 1, "Moderate": 2, "Severe": 3, "Critical": 4}
SEVERITY_SCORE = {"Minor": 25, "Moderate": 50, "Severe": 75, "Critical": 100}
ROAD_SCORE = {"Hospital / emergency route": 100, "Main road": 75, "Local road": 45}
COST = {"Minor": 2000, "Moderate": 7000, "Severe": 15000, "Critical": 35000}
EARTH_RADIUS_KM = 6371.0088


def severity_from_bbox(bbox, image_width=None, image_height=None, damage_type=""):
    """Estimate severity from normalized image footprint, not raw pixel count."""
    width = max(0.0, float(bbox[2]) - float(bbox[0]))
    height = max(0.0, float(bbox[3]) - float(bbox[1]))
    if not image_width or not image_height:
        area = width * height
        if area >= 70000: return "Critical"
        if area >= 35000: return "Severe"
        if area >= 12000: return "Moderate"
        return "Minor"

    area_ratio = (width * height) / max(float(image_width) * float(image_height), 1.0)
    longest_span = max(width / image_width, height / image_height)
    is_crack = "crack" in damage_type.lower()
    if is_crack:
        if area_ratio >= .12 or longest_span >= .72: return "Critical"
        if area_ratio >= .045 or longest_span >= .40: return "Severe"
        if area_ratio >= .012 or longest_span >= .20: return "Moderate"
    else:
        if area_ratio >= .13: return "Critical"
        if area_ratio >= .055: return "Severe"
        if area_ratio >= .018: return "Moderate"
    return "Minor"


def priority_label(score):
    return "Urgent" if score >= 80 else "High" if score >= 60 else "Medium" if score >= 40 else "Low"


def enrich_detections(raw, traffic, road_type):
    """Attach severity, explainable priority inputs, and stable simulated GPS."""
    locations = {}
    enriched = []
    for index, item in enumerate(raw, start=1):
        bbox = item["bbox"]
        center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        image_width = item.get("image_width") or max(bbox[2], 1)
        image_height = item.get("image_height") or max(bbox[3], 1)
        location_key = (item["damage_type"], round(center[0] / image_width, 2), round(center[1] / image_height, 2))
        if location_key not in locations:
            unique_index = len(locations)
            angle = unique_index * 2.4
            radius = .00035 + unique_index * .00018
            stable_random = random.Random(str(location_key))
            locations[location_key] = (
                32.7266 + math.cos(angle) * radius + stable_random.uniform(-.000015, .000015),
                74.8570 + math.sin(angle) * radius + stable_random.uniform(-.000015, .000015),
            )
        severity = severity_from_bbox(bbox, image_width, image_height, item["damage_type"])
        base_score = min(round(.45 * SEVERITY_SCORE[severity] + .25 * ROAD_SCORE[road_type] + .20 * traffic + .10 * (item["confidence"] * 100), 1), 100)
        latitude, longitude = locations[location_key]
        # Consecutive video observations receive tiny GPS jitter, then DBSCAN merges them.
        frame_jitter = (item.get("frame", 0) % 7) * .000002
        enriched.append({
            **item,
            "id": f"RD-{index:03}",
            "severity": severity,
            "priority_score": base_score,
            "priority": priority_label(base_score),
            "latitude": latitude + frame_jitter,
            "longitude": longitude - frame_jitter,
            "priority_factors": {"severity": SEVERITY_SCORE[severity], "road_importance": ROAD_SCORE[road_type], "traffic": traffic, "confidence": round(item["confidence"] * 100)},
        })
    return enriched


def remove_duplicates(detections, radius_meters=20):
    """Merge nearby observations by damage type using haversine DBSCAN."""
    if not detections:
        return []
    unique = []
    groups = defaultdict(list)
    for item in detections:
        groups[item["damage_type"]].append(item)
    for damage_type, typed_detections in groups.items():
        radians_coordinates = np.radians([[item["latitude"], item["longitude"]] for item in typed_detections])
        epsilon = (radius_meters / 1000) / EARTH_RADIUS_KM
        labels = DBSCAN(eps=epsilon, min_samples=1, metric="haversine").fit_predict(radians_coordinates)
        for cluster_id in sorted(set(labels)):
            cluster = [item for item, label in zip(typed_detections, labels) if label == cluster_id]
            representative = dict(max(cluster, key=lambda item: item["confidence"]))
            representative["duplicate_count"] = len(cluster)
            representative["latitude"] = sum(item["latitude"] for item in cluster) / len(cluster)
            representative["longitude"] = sum(item["longitude"] for item in cluster) / len(cluster)
            frequency_bonus = min(max(len(cluster) - 1, 0) * 2.5, 10)
            representative["priority_score"] = min(round(representative["priority_score"] + frequency_bonus, 1), 100)
            representative["priority"] = priority_label(representative["priority_score"])
            representative["priority_factors"] = {**representative.get("priority_factors", {}), "repeat_observations": len(cluster), "frequency_bonus": frequency_bonus}
            unique.append(representative)
    return sorted(unique, key=lambda item: item["priority_score"], reverse=True)


def build_summary(defects):
    raw_count = sum(item.get("duplicate_count", 1) for item in defects)
    damage_burden = sum(SEVERITY_POINTS[item["severity"]] * 8 for item in defects)
    road_health = max(0, min(100, round(100 - damage_burden)))
    health_label = "Excellent" if road_health >= 85 else "Good" if road_health >= 70 else "Needs maintenance" if road_health >= 50 else "Poor"
    return {
        "unique_defects": len(defects),
        "raw_detections": raw_count,
        "duplicates_removed": max(raw_count - len(defects), 0),
        "urgent_repairs": sum(item["priority"] == "Urgent" for item in defects),
        "estimated_cost": sum(COST[item["severity"]] for item in defects),
        "road_health_index": road_health,
        "health_label": health_label,
    }
