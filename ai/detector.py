"""Ultralytics model adapter with an explicitly labelled demo fallback."""
from functools import lru_cache
from pathlib import Path
import random

import cv2
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
MODEL_PATH = ROOT / "models" / "road_damage.pt"
OUTPUTS.mkdir(exist_ok=True)


@lru_cache(maxsize=1)
def _load_model():
    from ultralytics import YOLO
    return YOLO(str(MODEL_PATH))


def _class_name(index, names):
    name = names.get(index, str(index)) if isinstance(names, dict) else names[index]
    lowered = str(name).lower()
    if "pothole" in lowered: return "Pothole"
    if "alligator" in lowered: return "Alligator crack"
    if "transverse" in lowered: return "Transverse crack"
    if "longitudinal" in lowered: return "Longitudinal crack"
    return "Road crack"


def _detections_from_result(result, frame_index, image_width, image_height):
    detections = []
    for box in result.boxes:
        x1, y1, x2, y2 = [round(float(value), 1) for value in box.xyxy[0].tolist()]
        detections.append({"damage_type": _class_name(int(box.cls[0]), result.names), "confidence": float(box.conf[0]), "bbox": [x1, y1, x2, y2], "frame": frame_index, "image_width": image_width, "image_height": image_height})
    return detections


def _real_image(image_path):
    model = _load_model()
    result = model(str(image_path), conf=.30, verbose=False)[0]
    image_height, image_width = result.orig_shape
    detections = _detections_from_result(result, 0, image_width, image_height)
    output = OUTPUTS / f"annotated_{image_path.stem}.jpg"
    cv2.imwrite(str(output), result.plot())
    return detections, output


def _demo_image(image_path):
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    detections = [
        {"damage_type": "Pothole", "confidence": .92, "bbox": [width*.22, height*.55, width*.50, height*.84], "frame": 0, "image_width": width, "image_height": height},
        {"damage_type": "Longitudinal crack", "confidence": .84, "bbox": [width*.61, height*.34, width*.74, height*.77], "frame": 0, "image_width": width, "image_height": height},
    ]
    draw = ImageDraw.Draw(image)
    for item in detections:
        x1, y1, x2, y2 = map(int, item["bbox"])
        color = "#ef4444" if item["damage_type"] == "Pothole" else "#f97316"
        draw.rectangle((x1, y1, x2, y2), outline=color, width=max(3, width // 350))
        draw.rectangle((x1, max(y1-32, 0), min(x1+310, width), y1), fill=color)
        draw.text((x1+6, max(y1-27, 4)), f"{item['damage_type']} {item['confidence']:.0%}", fill="white")
    output = OUTPUTS / f"demo_annotated_{image_path.stem}.jpg"
    image.save(output, quality=92)
    return detections, output


def _real_video(video_path, sample_limit=24):
    capture = cv2.VideoCapture(str(video_path))
    frame_count = max(int(capture.get(cv2.CAP_PROP_FRAME_COUNT)), 1)
    stride = max(frame_count // sample_limit, 1)
    detections, best_plot, best_count = [], None, -1
    frame_index = 0
    model = _load_model()
    while capture.isOpened():
        ok, frame = capture.read()
        if not ok: break
        if frame_index % stride == 0:
            result = model(frame, conf=.30, verbose=False)[0]
            height, width = frame.shape[:2]
            frame_detections = _detections_from_result(result, frame_index, width, height)
            detections.extend(frame_detections)
            if len(frame_detections) > best_count:
                best_count, best_plot = len(frame_detections), result.plot()
        frame_index += 1
        if frame_index >= frame_count: break
    capture.release()
    if best_plot is None:
        raise ValueError("No readable frames were found in the uploaded video.")
    output = OUTPUTS / f"annotated_video_preview_{video_path.stem}.jpg"
    cv2.imwrite(str(output), best_plot)
    return detections, output


def _demo_video(video_path):
    capture = cv2.VideoCapture(str(video_path))
    ok, frame = capture.read()
    capture.release()
    if not ok: raise ValueError("Could not read the uploaded video.")
    preview = OUTPUTS / f"preview_{video_path.stem}.jpg"
    cv2.imwrite(str(preview), frame)
    detections, annotated = _demo_image(preview)
    expanded = []
    for item in detections:
        for frame_index in range(3):
            copy = dict(item)
            copy["frame"] = frame_index * 15
            copy["confidence"] = max(.5, copy["confidence"] - random.Random(f"{item['damage_type']}-{frame_index}").uniform(0, .04))
            expanded.append(copy)
    return expanded, annotated


def inspect_media(path, demo=False):
    is_video = path.suffix.lower() in {".mp4", ".avi", ".mov"}
    if demo and is_video: detections, output = _demo_video(path)
    elif demo: detections, output = _demo_image(path)
    elif is_video and MODEL_PATH.exists(): detections, output = _real_video(path)
    elif is_video: detections, output = _demo_video(path)
    elif MODEL_PATH.exists(): detections, output = _real_image(path)
    else: detections, output = _demo_image(path)
    mode = "guided sample (synthetic detections)" if demo else ("YOLO model" if MODEL_PATH.exists() else "demo fallback (add models/road_damage.pt for live YOLO)")
    return detections, output, mode
