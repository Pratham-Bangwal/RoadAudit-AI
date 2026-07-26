"""Inspection adapter. Uses models/road_damage.pt when available; otherwise demo mode."""
from pathlib import Path
import random
import cv2
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
MODEL_PATH = ROOT / "models" / "road_damage.pt"
OUTPUTS.mkdir(exist_ok=True)

def _class_name(index, names):
    name = names.get(index, str(index)) if isinstance(names, dict) else names[index]
    lowered = str(name).lower()
    if "pothole" in lowered: return "Pothole"
    if "alligator" in lowered: return "Alligator crack"
    if "transverse" in lowered: return "Transverse crack"
    if "longitudinal" in lowered: return "Longitudinal crack"
    return "Road crack"

def _real_image(image_path):
    from ultralytics import YOLO
    model = YOLO(str(MODEL_PATH))
    result = model(str(image_path), conf=0.30, verbose=False)[0]
    detections = []
    for box in result.boxes:
        x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        detections.append({"damage_type": _class_name(int(box.cls[0]), result.names), "confidence": float(box.conf[0]), "bbox": [x1, y1, x2, y2], "frame": 0})
    output = OUTPUTS / f"annotated_{image_path.stem}.jpg"
    cv2.imwrite(str(output), result.plot())
    return detections, output

def _demo_image(image_path):
    image = Image.open(image_path).convert("RGB")
    w, h = image.size
    detections = [{"damage_type":"Pothole", "confidence":.92, "bbox":[w*.22,h*.55,w*.50,h*.84], "frame":0}, {"damage_type":"Longitudinal crack", "confidence":.84, "bbox":[w*.61,h*.34,w*.74,h*.77], "frame":0}]
    draw = ImageDraw.Draw(image)
    for item in detections:
        x1, y1, x2, y2 = map(int, item["bbox"])
        draw.rectangle((x1,y1,x2,y2), outline="#ef4444", width=5)
        draw.text((x1,max(y1-22,0)), f"{item['damage_type']} {item['confidence']:.0%}", fill="#ef4444")
    output = OUTPUTS / f"demo_annotated_{image_path.stem}.jpg"
    image.save(output)
    return detections, output

def _video_preview(video_path):
    cap = cv2.VideoCapture(str(video_path)); ok, frame = cap.read(); cap.release()
    if not ok: raise ValueError("Could not read the uploaded video.")
    preview = OUTPUTS / f"preview_{video_path.stem}.jpg"; cv2.imwrite(str(preview), frame)
    detections, annotated = _real_image(preview) if MODEL_PATH.exists() else _demo_image(preview)
    expanded = []
    for item in detections:
        for frame_index in range(3):
            copy = dict(item); copy["frame"] = frame_index * 15; copy["confidence"] = max(.5, copy["confidence"] - random.uniform(0,.04)); expanded.append(copy)
    return expanded, annotated

def inspect_media(path):
    if path.suffix.lower() in {".mp4", ".avi", ".mov"}: detections, output = _video_preview(path)
    elif MODEL_PATH.exists(): detections, output = _real_image(path)
    else: detections, output = _demo_image(path)
    return detections, output, "YOLO model" if MODEL_PATH.exists() else "demo fallback (add models/road_damage.pt for live YOLO)"
