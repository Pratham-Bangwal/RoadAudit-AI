import argparse
import logging
import random
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def collect_images(image_root: Path) -> list[Path]:
    return sorted([p for p in image_root.iterdir() if p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS])


def build_label_map(label_root: Path) -> dict[str, Path]:
    label_map: dict[str, Path] = {}
    for label_path in label_root.rglob('*.txt'):
        label_map[label_path.name] = label_path
    return label_map


def copy_split_files(
    images: list[Path],
    label_map: dict[str, Path],
    split_name: str,
    output_images: Path,
    output_labels: Path,
) -> tuple[int, int, int]:
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    images_written = 0
    labels_written = 0
    missing_labels = 0

    for image_path in images:
        label_name = image_path.with_suffix('.txt').name
        if label_name not in label_map:
            missing_labels += 1
            continue

        destination_image = output_images / image_path.name
        destination_label = output_labels / label_name

        shutil.copy2(image_path, destination_image)
        shutil.copy2(label_map[label_name], destination_label)

        images_written += 1
        labels_written += 1

    return images_written, labels_written, missing_labels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Split a processed image/label dataset into train and validation sets.'
    )
    parser.add_argument(
        '--images',
        type=Path,
        default=Path('dataset/processed/images'),
        help='Path to the flat processed image directory.',
    )
    parser.add_argument(
        '--labels',
        type=Path,
        default=Path('dataset/processed/labels'),
        help='Path to the flat processed label directory.',
    )
    parser.add_argument(
        '--output-root',
        type=Path,
        default=Path('dataset/processed'),
        help='Path to the processed dataset root for split output.',
    )
    parser.add_argument(
        '--val-ratio',
        type=float,
        default=0.2,
        help='Validation split ratio.',
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for dataset shuffling.',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.images.exists():
        raise FileNotFoundError(f'Image directory not found: {args.images}')
    if not args.labels.exists():
        raise FileNotFoundError(f'Label directory not found: {args.labels}')

    output_images_root = args.output_root / 'images'
    output_labels_root = args.output_root / 'labels'

    images = collect_images(args.images)
    label_map = build_label_map(args.labels)

    matched_images = [img for img in images if img.with_suffix('.txt').name in label_map]
    unmatched_images = len(images) - len(matched_images)

    random.Random(args.seed).shuffle(matched_images)
    val_count = int(len(matched_images) * args.val_ratio)
    val_images = matched_images[:val_count]
    train_images = matched_images[val_count:]

    train_image_count, train_label_count, train_missing = copy_split_files(
        train_images,
        label_map,
        'train',
        output_images_root / 'train',
        output_labels_root / 'train',
    )
    val_image_count, val_label_count, val_missing = copy_split_files(
        val_images,
        label_map,
        'val',
        output_images_root / 'val',
        output_labels_root / 'val',
    )

    logging.info('Train images copied : %d', train_image_count)
    logging.info('Train labels copied : %d', train_label_count)
    logging.info('Val images copied   : %d', val_image_count)
    logging.info('Val labels copied   : %d', val_label_count)
    logging.info('Unmatched images    : %d', unmatched_images)
    logging.info('Missing labels      : %d', train_missing + val_missing)


if __name__ == '__main__':
    main()
