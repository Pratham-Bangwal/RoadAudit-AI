import argparse
import logging
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def collect_files(root: Path, exts: set[str]) -> list[Path]:
    return sorted([p for p in root.rglob('*') if p.suffix.lower() in exts])


def count_label_files(label_root: Path) -> tuple[int, Counter[str], int, int, set[str]]:
    class_counts: Counter[str] = Counter()
    empty_labels = 0
    ignored_classes: set[str] = set()
    total_labels = 0

    for label_path in label_root.rglob('*.txt'):
        total_labels += 1
        text = label_path.read_text().strip()
        if not text:
            empty_labels += 1
            continue
        for line in text.splitlines():
            parts = line.split()
            if not parts:
                continue
            class_id = parts[0]
            class_counts[class_id] += 1
            if class_id not in {'0', '1', '2', '3'}:
                ignored_classes.add(class_id)

    return total_labels, class_counts, empty_labels, len(ignored_classes), ignored_classes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Print statistics for the processed YOLO dataset.'
    )
    parser.add_argument(
        '--processed-root',
        type=Path,
        default=Path('dataset/processed'),
        help='Root of the processed dataset.',
    )
    parser.add_argument(
        '--image-exts',
        nargs='+',
        default=list(SUPPORTED_IMAGE_EXTENSIONS),
        help='Image file extensions to count.',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    processed_root = args.processed_root
    images_root = processed_root / 'images'
    labels_root = processed_root / 'labels'

    if not images_root.exists() or not labels_root.exists():
        raise FileNotFoundError('Processed images and labels directories must exist.')

    train_images = collect_files(images_root / 'train', set(args.image_exts))
    val_images = collect_files(images_root / 'val', set(args.image_exts))
    train_labels = list((labels_root / 'train').rglob('*.txt'))
    val_labels = list((labels_root / 'val').rglob('*.txt'))

    train_total, train_classes, train_empty, train_ignored_count, train_ignored = count_label_files(labels_root / 'train')
    val_total, val_classes, val_empty, val_ignored_count, val_ignored = count_label_files(labels_root / 'val')

    missing_train = len([img for img in train_images if not (labels_root / 'train' / img.with_suffix('.txt').name).exists()])
    missing_val = len([img for img in val_images if not (labels_root / 'val' / img.with_suffix('.txt').name).exists()])

    logging.info('Images')
    logging.info('  Train      : %d', len(train_images))
    logging.info('  Validation : %d', len(val_images))
    logging.info('Labels')
    logging.info('  Train      : %d', len(train_labels))
    logging.info('  Validation : %d', len(val_labels))
    logging.info('Per-class counts (train)')
    for cls_id, count in sorted(train_classes.items(), key=lambda item: int(item[0])):
        logging.info('  %s: %d', cls_id, count)
    logging.info('Per-class counts (val)')
    for cls_id, count in sorted(val_classes.items(), key=lambda item: int(item[0])):
        logging.info('  %s: %d', cls_id, count)
    logging.info('Missing labels')
    logging.info('  Train : %d', missing_train)
    logging.info('  Val   : %d', missing_val)
    logging.info('Empty labels')
    logging.info('  Train : %d', train_empty)
    logging.info('  Val   : %d', val_empty)
    logging.info('Ignored classes')
    logging.info('  Train : %d %s', train_ignored_count, sorted(train_ignored))
    logging.info('  Val   : %d %s', val_ignored_count, sorted(val_ignored))


if __name__ == '__main__':
    main()
