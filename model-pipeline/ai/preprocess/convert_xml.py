from pathlib import Path
import argparse
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

CLASS_MAP = {
    'D00': 0,  # Longitudinal Crack
    'D10': 1,  # Transverse Crack
    'D20': 2,  # Alligator Crack
    'D40': 3,  # Pothole
}


def load_voc_annotation(annotation_path: Path) -> list[tuple[int, float, float, float, float]]:
    root = ET.parse(annotation_path).getroot()
    size = root.find('size')
    width = int(size.findtext('width'))
    height = int(size.findtext('height'))

    labels: list[tuple[int, float, float, float, float]] = []
    for obj in root.findall('object'):
        label_name = obj.findtext('name')
        if label_name not in CLASS_MAP:
            continue

        bbox = obj.find('bndbox')
        xmin = float(bbox.findtext('xmin'))
        ymin = float(bbox.findtext('ymin'))
        xmax = float(bbox.findtext('xmax'))
        ymax = float(bbox.findtext('ymax'))

        x_center = ((xmin + xmax) / 2.0) / width
        y_center = ((ymin + ymax) / 2.0) / height
        box_width = (xmax - xmin) / width
        box_height = (ymax - ymin) / height

        labels.append((CLASS_MAP[label_name], x_center, y_center, box_width, box_height))

    return labels


def build_yolo_lines(labels: list[tuple[int, float, float, float, float]]) -> list[str]:
    return [
        f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
        for cls_id, x_center, y_center, width, height in labels
    ]


def write_label_file(yolo_lines: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(yolo_lines))


def convert_voc_file(xml_path: Path, destination_root: Path, source_root: Path) -> None:
    yolo_lines = build_yolo_lines(load_voc_annotation(xml_path))
    if not yolo_lines:
        logging.debug("Skipping %s because no mapped labels were found.", xml_path.name)
        return

    relative_path = xml_path.relative_to(source_root).with_suffix('.txt')
    destination_path = destination_root / relative_path
    write_label_file(yolo_lines, destination_path)
    logging.info('Converted %s -> %s', xml_path.name, destination_path.name)


def collect_voc_files(source_dir: Path) -> list[Path]:
    return sorted(source_dir.rglob('*.xml'))


def convert_directory(source_dir: Path, destination_dir: Path) -> int:
    xml_files = collect_voc_files(source_dir)
    for xml_path in xml_files:
        convert_voc_file(xml_path, destination_dir, source_dir)
    return len(xml_files)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Convert Pascal VOC XML annotations to YOLO TXT labels.'
    )
    parser.add_argument(
        '--source',
        type=Path,
        required=True,
        help='Path to the directory containing VOC XML annotations.',
    )
    parser.add_argument(
        '--dest',
        type=Path,
        required=True,
        help='Path where YOLO TXT labels should be written.',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.source.exists():
        raise FileNotFoundError(f'Source directory not found: {args.source}')

    converted_count = convert_directory(args.source, args.dest)
    logging.info(
        'Converted %d XML files to YOLO TXT labels in %s',
        converted_count,
        args.dest,
    )


if __name__ == '__main__':
    main()
