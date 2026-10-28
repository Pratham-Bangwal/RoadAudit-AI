"""Train a YOLOv11 road-damage detector."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import torch
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = PROJECT_ROOT.parent / "models" / "road_damage.pt"
DEFAULT_DATASET = PROJECT_ROOT / "dataset" / "processed" / "dataset.yaml"
DEFAULT_RUNS_DIR = PROJECT_ROOT / "runs"


def configure_logging(verbose: bool) -> None:
    """Configure application logging once for the training process."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def validate_training_paths(model_path: Path, dataset_path: Path) -> None:
    """Ensure required local training inputs are available before training."""
    if not model_path.is_file():
        raise FileNotFoundError(f"YOLO model weights not found: {model_path}")
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset configuration not found: {dataset_path}")


def resolve_device(requested_device: str) -> str:
    """Choose a supported device, using the first CUDA GPU when available."""
    if requested_device != "auto":
        return requested_device

    if torch.cuda.is_available():
        logging.info("CUDA is available; using GPU 0.")
        return "0"

    logging.warning("CUDA is unavailable; using CPU training. Use --device 0 after installing CUDA PyTorch.")
    return "cpu"


def train_model(
    model_path: Path,
    dataset_path: Path,
    epochs: int,
    image_size: int,
    batch_size: int,
    workers: int,
    device: str,
    output_dir: Path,
    run_name: str,
) -> dict[str, Any]:
    """Train YOLO and return the Ultralytics training results."""
    validate_training_paths(model_path, dataset_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    device = resolve_device(device)

    logging.info("Loading model weights from %s", model_path)
    model = YOLO(model_path)
    logging.info(
        "Starting training: epochs=%d, imgsz=%d, batch=%d, workers=%d, device=%s",
        epochs,
        image_size,
        batch_size,
        workers,
        device,
    )

    return model.train(
        data=str(dataset_path),
        epochs=epochs,
        imgsz=image_size,
        batch=batch_size,
        workers=workers,
        device=device,
        project=str(output_dir),
        name=run_name,
        exist_ok=False,
        save=True,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for training options."""
    parser = argparse.ArgumentParser(description="Train a YOLOv11 road-damage detector.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="Starting YOLO weights.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET, help="YOLO dataset YAML file.")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs.")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size.")
    parser.add_argument("--batch", type=int, default=8, help="Training batch size.")
    parser.add_argument("--workers", type=int, default=4, help="Data loader worker count.")
    parser.add_argument(
        "--device",
        default="auto",
        help="Training device: auto (GPU 0 when available, otherwise CPU), 0, cpu, or 0,1.",
    )
    parser.add_argument("--project", type=Path, default=DEFAULT_RUNS_DIR, help="Training runs directory.")
    parser.add_argument("--name", default="road_damage_yolo11n", help="Name for this training run.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def main() -> None:
    """Parse arguments, train the model, and report generated checkpoints."""
    args = build_parser().parse_args()
    configure_logging(args.verbose)

    if min(args.epochs, args.imgsz, args.batch, args.workers) < 1:
        raise ValueError("epochs, imgsz, batch, and workers must all be positive integers")

    results = train_model(
        model_path=args.model,
        dataset_path=args.data,
        epochs=args.epochs,
        image_size=args.imgsz,
        batch_size=args.batch,
        workers=args.workers,
        device=args.device,
        output_dir=args.project,
        run_name=args.name,
    )

    save_dir = Path(results.save_dir)
    logging.info("Training completed. Best checkpoint: %s", save_dir / "weights" / "best.pt")
    logging.info("Training completed. Last checkpoint: %s", save_dir / "weights" / "last.pt")


if __name__ == "__main__":
    main()
