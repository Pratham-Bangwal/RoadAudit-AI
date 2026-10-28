"""Create a smaller reproducible dataset for time-constrained MVP training."""

from __future__ import annotations

import argparse
import logging
import random
import shutil
from pathlib import Path

import yaml


CLASS_NAMES = [
    "Longitudinal_Crack",
    "Transverse_Crack",
    "Alligator_Crack",
    "Pothole",
]


def copy_split(source_root: Path, target_root: Path, split: str, count: int, seed: int) -> int:
    """Copy a seeded random sample of matched image-label pairs for one split."""
    source_images = source_root / "images" / split
    source_labels = source_root / "labels" / split
    target_images = target_root / "images" / split
    target_labels = target_root / "labels" / split
    target_images.mkdir(parents=True, exist_ok=True)
    target_labels.mkdir(parents=True, exist_ok=True)

    pairs = [
        image_path
        for image_path in source_images.iterdir()
        if image_path.is_file() and (source_labels / f"{image_path.stem}.txt").is_file()
    ]
    if count > len(pairs):
        raise ValueError(f"Requested {count} {split} images, but only found {len(pairs)} matched pairs")

    selected = random.Random(seed).sample(sorted(pairs), count)
    for image_path in selected:
        label_path = source_labels / f"{image_path.stem}.txt"
        shutil.copy2(image_path, target_images / image_path.name)
        shutil.copy2(label_path, target_labels / label_path.name)
    return len(selected)


def write_dataset_yaml(output_root: Path, output_yaml: Path) -> None:
    """Write the YOLO configuration for the MVP subset."""
    data = {
        "path": output_root.as_posix(),
        "train": "images/train",
        "val": "images/val",
        "names": {index: name for index, name in enumerate(CLASS_NAMES)},
    }
    output_yaml.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a sampled YOLO dataset for MVP training.")
    parser.add_argument("--source", type=Path, default=Path("dataset/processed"))
    parser.add_argument("--output", type=Path, default=Path("dataset/mvp"))
    parser.add_argument("--train-count", type=int, default=2000)
    parser.add_argument("--val-count", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = build_parser().parse_args()
    if args.output.exists():
        raise FileExistsError(f"Output directory already exists: {args.output}")

    train_count = copy_split(args.source, args.output, "train", args.train_count, args.seed)
    val_count = copy_split(args.source, args.output, "val", args.val_count, args.seed)
    write_dataset_yaml(args.output, args.output / "dataset.yaml")
    logging.info("Created MVP subset: %d train images and %d validation images at %s", train_count, val_count, args.output)


if __name__ == "__main__":
    main()
