"""Run road-damage detection over a video and export annotated results."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO

from inference import DEFAULT_MODEL, build_detection_payload


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "video_inference"


def process_video(
    model_path: Path,
    video_path: Path,
    output_dir: Path,
    confidence: float,
    frame_stride: int,
) -> tuple[Path, Path]:
    """Detect road damage per sampled frame and export video plus JSON results."""
    if not model_path.is_file():
        raise FileNotFoundError(f"Model weights not found: {model_path}")
    if not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if frame_stride < 1:
        raise ValueError("frame_stride must be a positive integer")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        capture.release()
        raise RuntimeError(f"Unable to read video dimensions: {video_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_video_path = output_dir / f"{video_path.stem}_annotated.mp4"
    json_path = output_dir / f"{video_path.stem}_detections.json"
    writer = cv2.VideoWriter(
        str(annotated_video_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Unable to create output video: {annotated_video_path}")

    model = YOLO(model_path)
    frames: list[dict[str, Any]] = []
    frame_index = 0
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            if frame_index % frame_stride == 0:
                result = model.predict(source=frame, conf=confidence, verbose=False)[0]
                frame_source = Path(f"{video_path.stem}_frame_{frame_index:06d}.jpg")
                payload = build_detection_payload(result, frame_source)
                payload["frame_index"] = frame_index
                payload["timestamp_seconds"] = round(frame_index / fps, 3)
                frames.append(payload)
                annotated_frame = result.plot()
            else:
                annotated_frame = frame

            writer.write(annotated_frame)
            frame_index += 1
    finally:
        capture.release()
        writer.release()

    output = {
        "video_id": video_path.name,
        "fps": round(fps, 3),
        "frame_stride": frame_stride,
        "processed_frames": len(frames),
        "frames": frames,
    }
    json_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    logging.info("Processed %d frames from %s", len(frames), video_path)
    logging.info("Saved annotated video to %s", annotated_video_path)
    logging.info("Saved frame detections to %s", json_path)
    return annotated_video_path, json_path


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for video inference."""
    parser = argparse.ArgumentParser(description="Run YOLOv11 road-damage video inference.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="YOLO checkpoint path.")
    parser.add_argument("--video", type=Path, required=True, help="Input road video path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for outputs.")
    parser.add_argument("--conf", type=float, default=0.25, help="Minimum detection confidence.")
    parser.add_argument("--frame-stride", type=int, default=1, help="Process every Nth frame.")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = build_parser().parse_args()
    process_video(args.model, args.video, args.output_dir, args.conf, args.frame_stride)


if __name__ == "__main__":
    main()
