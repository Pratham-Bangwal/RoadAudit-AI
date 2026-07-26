"""Evidence fingerprinting helpers used by repair verification."""
from pathlib import Path

import cv2
import numpy as np


HASH_SIZE = 16


def _reference_frame(path):
    """Return a representative BGR frame for an image or video."""
    path = Path(path)
    image = cv2.imread(str(path))
    if image is not None:
        return image

    capture = cv2.VideoCapture(str(path))
    try:
        ok, frame = capture.read()
        if ok and frame is not None:
            return frame
    finally:
        capture.release()
    raise ValueError("Evidence could not be decoded as an image or video.")


def evidence_fingerprint(path):
    """Create a compact perceptual difference hash for inspection evidence."""
    frame = _reference_frame(path)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (HASH_SIZE + 1, HASH_SIZE), interpolation=cv2.INTER_AREA)
    bits = resized[:, 1:] > resized[:, :-1]
    packed = np.packbits(bits.astype(np.uint8).reshape(-1))
    return packed.tobytes().hex()


def fingerprint_similarity(first, second):
    """Return perceptual similarity from 0.0 (different) to 1.0 (identical)."""
    if not first or not second:
        return None
    try:
        first_bytes = bytes.fromhex(first)
        second_bytes = bytes.fromhex(second)
    except (TypeError, ValueError):
        return None
    if len(first_bytes) != len(second_bytes) or not first_bytes:
        return None
    different_bits = sum((left ^ right).bit_count() for left, right in zip(first_bytes, second_bytes))
    return round(1 - different_bits / (len(first_bytes) * 8), 4)
