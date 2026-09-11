"""
CelebA attribute + landmark loader for Experiment 1A.

Reads Expermiment/list_attr_celeba.txt and list_landmarks_align_celeba.txt
keyed by image id (e.g. 001089.jpg).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPERIMENT_ASSETS = ROOT / "Expermiment"


def _parse_attr_header(header_line: str) -> list[str]:
    return header_line.strip().split()


def load_celeba_attributes(
    image_id: str,
    attr_path: Path | None = None,
) -> dict[str, bool]:
    """
    Return {attr_name: True/False} for one image.
    CelebA encoding: 1 → True, -1 → False.
    """
    path = attr_path or (DEFAULT_EXPERIMENT_ASSETS / "list_attr_celeba.txt")
    if not path.is_file():
        raise FileNotFoundError(f"CelebA attr file not found: {path}")

    with path.open("r", encoding="utf-8", errors="replace") as f:
        _n = f.readline()  # count line
        header = f.readline()
        names = _parse_attr_header(header)
        target = image_id.strip()
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] != target:
                continue
            vals = parts[1:]
            if len(vals) != len(names):
                raise ValueError(
                    f"Attr length mismatch for {target}: "
                    f"{len(vals)} values vs {len(names)} names"
                )
            return {name: int(v) == 1 for name, v in zip(names, vals)}

    raise KeyError(f"Image id not found in attr file: {image_id}")


def load_celeba_landmarks(
    image_id: str,
    landmark_path: Path | None = None,
) -> dict[str, list[int]]:
    """
    Return 5-point landmarks for one image:
      left_eye, right_eye, nose, left_mouth, right_mouth
    """
    path = landmark_path or (
        DEFAULT_EXPERIMENT_ASSETS / "list_landmarks_align_celeba.txt"
    )
    if not path.is_file():
        raise FileNotFoundError(f"CelebA landmark file not found: {path}")

    with path.open("r", encoding="utf-8", errors="replace") as f:
        _n = f.readline()
        _header = f.readline()
        target = image_id.strip()
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] != target:
                continue
            nums = [int(x) for x in parts[1:]]
            if len(nums) != 10:
                raise ValueError(f"Expected 10 landmark coords for {target}, got {len(nums)}")
            return {
                "left_eye": [nums[0], nums[1]],
                "right_eye": [nums[2], nums[3]],
                "nose": [nums[4], nums[5]],
                "left_mouth": [nums[6], nums[7]],
                "right_mouth": [nums[8], nums[9]],
            }

    raise KeyError(f"Image id not found in landmark file: {image_id}")


def load_raw_attr_line(
    image_id: str,
    attr_path: Path | None = None,
) -> tuple[str, str]:
    """Return (header_line, data_line) for audit copy into celeba_attributes.txt."""
    path = attr_path or (DEFAULT_EXPERIMENT_ASSETS / "list_attr_celeba.txt")
    with path.open("r", encoding="utf-8", errors="replace") as f:
        _n = f.readline()
        header = f.readline().rstrip("\n")
        target = image_id.strip()
        for line in f:
            if line.split()[:1] == [target]:
                return header, line.rstrip("\n")
    raise KeyError(f"Image id not found: {image_id}")


def build_ground_truth(
    image_id: str,
    attrs: dict[str, bool] | None = None,
    landmarks: dict[str, list[int]] | None = None,
    unavailable_for_interview: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble ground_truth.json payload (all CelebA attrs kept as booleans)."""
    attrs = attrs or load_celeba_attributes(image_id)
    landmarks = landmarks or load_celeba_landmarks(image_id)
    return {
        "source": "CelebA",
        "image_id": image_id,
        "available_attributes": dict(attrs),
        "landmarks": landmarks,
        "unavailable_for_interview": unavailable_for_interview
        or [
            "nose.bridge",
            "chin.projection",
            "ears.protrusion",
            "forehead.slope",
            "eyes.color",
        ],
    }


if __name__ == "__main__":
    iid = "001089.jpg"
    a = load_celeba_attributes(iid)
    lm = load_celeba_landmarks(iid)
    print("attrs true:", sorted(k for k, v in a.items() if v))
    print("landmarks:", lm)
