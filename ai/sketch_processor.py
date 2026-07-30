"""
Report Phase 4 — Sketch Style Transfer (classic pencil polish).

Matches the STAAR / Forensic Sketch Generator report:
  - Edge detection (Laplacian / Canny)
  - Gaussian blur blending
  - Dodge & Burn layer compositing

IMPORTANT: This is a *light polish* after SD img2img has already created
a graphite pencil look. It must NOT use adaptiveThreshold / pencilSketch
mesh filters (those caused the muddy cross-hatch outputs).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from utils.config import settings


def apply_pencil_sketch(image: Image.Image, **_kwargs) -> Image.Image:
    """
    Soft graphite polish via dodge & burn + light edges.

    Prefer calling this on an SD img2img pencil result, not a raw photo.
    """
    if not settings.sketch_polish:
        return image.convert("RGB")

    rgb = np.array(image.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Gentle denoise so dodge-burn stays smooth (pencil, not grain)
    gray = cv2.medianBlur(gray, 3)

    # --- Dodge & Burn (report) ---
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (0, 0), sigmaX=float(settings.sketch_sigma))
    blurred = np.maximum(blurred, 1)
    dodge = cv2.divide(gray, 255 - blurred, scale=256.0)

    # --- Edge detection (Laplacian, report) — very light ---
    lap = cv2.Laplacian(gray, cv2.CV_16S, ksize=3)
    lap = cv2.convertScaleAbs(lap)
    # Soft line layer on white paper polarity
    edges = 255 - cv2.GaussianBlur(lap, (3, 3), 0)

    edge_w = float(settings.sketch_edge_blend)
    sketch = cv2.addWeighted(dodge, 1.0 - edge_w, edges, edge_w, 0)

    # Mild contrast for readable features on white paper
    clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
    sketch = clahe.apply(sketch)
    sketch = cv2.convertScaleAbs(sketch, alpha=1.05, beta=8)

    # Desaturate safety — ensure pure graphite RGB
    return Image.fromarray(sketch).convert("RGB")


def save_sketch(image: Image.Image, prefix: str = "sketch", directory: Path | None = None) -> Path:
    out_dir = Path(directory or settings.outputs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if prefix.startswith("sketch_") and prefix.count("_") >= 2:
        filename = f"{prefix}.png"
    else:
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = out_dir / filename
    image.save(path)
    return path
