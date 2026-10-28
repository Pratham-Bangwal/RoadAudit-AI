"""Run road-damage inference and export annotated and JSON results."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from road_health import compute_road_health_index
from severity import assess_severity


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = PROJECT_ROOT.parent / "models" / "road_damage.pt"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "inference"


def build_detection_payload(result: Any, image_path: Path) -> dict[str, Any]:
    """Convert an Ultralytics result into a backend-friendly JSON payload."""
    detections = []
    names = result.names
    image_height, image_width = result.orig_shape
    for box in result.boxes:
        class_id = int(box.cls.item())
        confidence = float(box.conf.item())
        bbox_xyxy = [round(float(value), 2) for value in box.xyxy[0].tolist()]
        detections.append(
            {
                "class_id": class_id,
                "class": names[class_id],
                "confidence": round(confidence, 4),
                "bbox_xyxy": bbox_xyxy,
                "severity": assess_severity(names[class_id], bbox_xyxy, (image_height, image_width), confidence),
            }
        )

    return {
        "image_id": image_path.name,
        "detections": detections,
        "road_health_index": compute_road_health_index(detections),
        "road_health_index_method": "mvp_severity_weighted_penalty",
    }


def run_inference(
    model_path: Path,
    image_path: Path,
    output_dir: Path,
    confidence: float,
) -> tuple[Path, Path]:
    """Run detection and save an annotated image plus a JSON response payload."""
    if not model_path.is_file():
        raise FileNotFoundError(f"Model weights not found: {model_path}")
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")

    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(model_path)
    result = model.predict(source=str(image_path), conf=confidence, verbose=False)[0]

    annotated_path = output_dir / f"{image_path.stem}_annotated{image_path.suffix}"
    result.save(filename=str(annotated_path))

    json_path = output_dir / f"{image_path.stem}_detections.json"
    json_path.write_text(
        json.dumps(build_detection_payload(result, image_path), indent=2),
        encoding="utf-8",
    )
    logging.info("Saved annotated image to %s", annotated_path)
    logging.info("Saved detection JSON to %s", json_path)
    return annotated_path, json_path


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for image inference."""
    parser = argparse.ArgumentParser(description="Run YOLOv11 road-damage image inference.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="YOLO checkpoint path.")
    parser.add_argument("--image", type=Path, required=True, help="Input road image path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for outputs.")
    parser.add_argument("--conf", type=float, default=0.25, help="Minimum detection confidence.")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = build_parser().parse_args()
    run_inference(args.model, args.image, args.output_dir, args.conf)


if __name__ == "__main__":
    main()
