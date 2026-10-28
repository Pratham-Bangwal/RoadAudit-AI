import argparse
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def collect_label_files(label_root: Path) -> dict[str, Path]:
    label_files: dict[str, Path] = {}
    for label_path in label_root.rglob('*.txt'):
        if label_path.parent == label_root:
            continue
        if label_path.name in label_files:
            logging.warning(
                'Duplicate label name detected: %s (keeping %s, skipping %s)',
                label_path.name,
                label_files[label_path.name],
                label_path,
            )
            continue
        label_files[label_path.name] = label_path
    return label_files


def collect_image_files(source_root: Path, ignore_dirs: set[str] | None = None) -> tuple[list[Path], int]:
    image_files: list[Path] = []
    ignored_count = 0
    for image_path in source_root.rglob('*'):
        if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        if ignore_dirs and any(part.lower() in ignore_dirs for part in image_path.parts):
            ignored_count += 1
            continue
        image_files.append(image_path)
    return image_files, ignored_count


def copy_matched_images(
    source_root: Path,
    label_root: Path,
    output_images: Path,
    output_labels: Path,
    ignore_dirs: set[str] | None = None,
) -> tuple[int, int, int, int]:
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    label_files = collect_label_files(label_root)
    images_copied = 0
    labels_copied = 0
    missing_labels = 0

    image_paths, ignored_images = collect_image_files(source_root, ignore_dirs=ignore_dirs)
    for image_path in image_paths:
        label_name = image_path.with_suffix('.txt').name
        if label_name not in label_files:
            missing_labels += 1
            continue

        destination_image = output_images / image_path.name
        if not destination_image.exists():
            shutil.copy2(image_path, destination_image)
        images_copied += 1

        label_source = label_files[label_name]
        destination_label = output_labels / label_source.name
        if not destination_label.exists():
            shutil.copy2(label_source, destination_label)
            labels_copied += 1

    return images_copied, labels_copied, missing_labels, ignored_images


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Merge RDD2022 country images into a single processed dataset and match them with YOLO labels.'
    )
    parser.add_argument(
        '--source',
        type=Path,
        default=Path('dataset/RDD2022_all_countries'),
        help='Path to the root of the RDD2022_all_countries dataset.',
    )
    parser.add_argument(
        '--label-root',
        type=Path,
        default=Path('dataset/processed/labels'),
        help='Path to the converted YOLO label tree.',
    )
    parser.add_argument(
        '--output-root',
        type=Path,
        default=Path('dataset/processed'),
        help='Path to the processed dataset output root.',
    )
    parser.add_argument(
        '--ignore-tests',
        action='store_true',
        help='Skip image files under directories named "test" when merging the dataset.',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.source.exists():
        raise FileNotFoundError(f'Source dataset root not found: {args.source}')
    if not args.label_root.exists():
        raise FileNotFoundError(f'Label root not found: {args.label_root}')

    output_images = args.output_root / 'images'
    output_labels = args.output_root / 'labels'
    ignore_dirs = {'test'} if args.ignore_tests else None

    images_copied, labels_copied, missing_labels, ignored_images = copy_matched_images(
        args.source,
        args.label_root,
        output_images,
        output_labels,
        ignore_dirs=ignore_dirs,
    )

    logging.info('Images copied : %d', images_copied)
    logging.info('Labels copied : %d', labels_copied)
    logging.info('Missing labels : %d', missing_labels)
    if args.ignore_tests:
        logging.info('Ignored test images : %d', ignored_images)


if __name__ == '__main__':
    main()
