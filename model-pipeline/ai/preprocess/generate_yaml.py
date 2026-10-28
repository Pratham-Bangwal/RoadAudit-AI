import argparse
import logging
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DEFAULT_CLASS_NAMES = [
    'Longitudinal_Crack',
    'Transverse_Crack',
    'Alligator_Crack',
    'Pothole',
]


def generate_dataset_yaml(processed_root: Path, class_names: list[str], output_path: Path) -> Path:
    data = {
        'path': str(processed_root).replace('\\', '/'),
        'train': 'images/train',
        'val': 'images/val',
        'names': {idx: name for idx, name in enumerate(class_names)},
    }
    output_path.write_text(yaml.safe_dump(data, sort_keys=False))
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Generate a YOLO dataset YAML config for the processed dataset.'
    )
    parser.add_argument(
        '--processed-root',
        type=Path,
        default=Path('dataset/processed'),
        help='Root for the processed dataset.',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('dataset/processed/dataset.yaml'),
        help='Output YAML file path.',
    )
    parser.add_argument(
        '--classes',
        nargs='+',
        default=DEFAULT_CLASS_NAMES,
        help='List of class names to include in the YAML config.',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.processed_root.exists():
        raise FileNotFoundError(f'Processed dataset root not found: {args.processed_root}')

    output_path = generate_dataset_yaml(args.processed_root, args.classes, args.output)
    logging.info('Generated dataset YAML at %s', output_path)


if __name__ == '__main__':
    main()
