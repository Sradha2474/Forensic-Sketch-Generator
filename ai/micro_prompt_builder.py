"""
Micro prompt builder (Python) — Experiment 1B / CLIP ≤77.

Builds a short identity prompt from structured_values dicts
(same shape as FaceProfile.structured_values from the Next.js UI).

Does not replace ai/prompt_builder.py (WitnessProfile / SD legacy).
"""

from __future__ import annotations

from typing import Any

SKIP = frozenset({"none", "unknown", "not_available", ""})
CLIP_SOFT_MAX = 70


def approx_token_count(text: str) -> int:
    return len([t for t in text.strip().split() if t])


def clip_truncate(text: str, max_tokens: int = CLIP_SOFT_MAX) -> str:
    tokens = [t for t in text.strip().split() if t]
    if len(tokens) <= max_tokens:
        return " ".join(tokens)
    return " ".join(tokens[:max_tokens])


def _v(structured: dict[str, Any], group: str, field: str) -> str | None:
    g = structured.get(group) or {}
    if not isinstance(g, dict):
        return None
    raw = g.get(field)
    if raw is None:
        return None
    s = str(raw).strip().replace("_", " ")
    if not s or s.lower() in SKIP:
        return None
    return s


def generate_micro_prompt(
    structured_values: dict[str, Any],
) -> tuple[str, str]:
    """
    Return (positive, negative) micro prompt from structured_values.
    """
    parts: list[str] = [
        "forensic face portrait",
        "front view",
        "mugshot",
    ]
    s = structured_values or {}

    age = _v(s, "age", "range")
    if age:
        parts.append(age)
    wrinkles = _v(s, "age", "wrinkles")
    if wrinkles:
        parts.append(f"{wrinkles} wrinkles")

    shape = _v(s, "face", "shape")
    if shape:
        parts.append(f"{shape} face")
    face_w = _v(s, "face", "width")
    if face_w:
        parts.append(f"{face_w} width")
    face_l = _v(s, "face", "length")
    if face_l:
        parts.append(f"{face_l} length")

    hair_bits = [
        _v(s, "hair", "color"),
        _v(s, "hair", "length"),
        _v(s, "hair", "texture"),
    ]
    hair_bits = [b for b in hair_bits if b]
    if hair_bits:
        parts.append(f"{' '.join(hair_bits)} hair")

    eye_bits = [
        _v(s, "eyes", "size"),
        _v(s, "eyes", "shape"),
        _v(s, "eyes", "color"),
        _v(s, "eyes", "spacing"),
    ]
    eye_bits = [b for b in eye_bits if b]
    if eye_bits:
        parts.append(f"{' '.join(eye_bits)} eyes")

    nose_bits = [
        _v(s, "nose", "length"),
        _v(s, "nose", "width"),
        _v(s, "nose", "bridge"),
        _v(s, "nose", "tip"),
    ]
    nose_bits = [b for b in nose_bits if b]
    if nose_bits:
        parts.append(f"{' '.join(nose_bits)} nose")

    jaw_w = _v(s, "jaw", "width")
    jaw_s = _v(s, "jaw", "shape")
    if jaw_w or jaw_s:
        parts.append(f"{' '.join(x for x in (jaw_w, jaw_s) if x)} jaw")

    beard = _v(s, "facial_hair", "beard")
    if beard:
        parts.append(f"{beard} beard")
    moustache = _v(s, "facial_hair", "moustache")
    if moustache:
        parts.append(f"{moustache} moustache")

    glasses = _v(s, "accessories", "glasses")
    if glasses and glasses.lower() != "no":
        parts.append(f"glasses {glasses}")

    scars = _v(s, "marks", "scars")
    if scars:
        parts.append(f"scar {scars}")

    expression = _v(s, "context", "expression")
    if expression:
        parts.append(expression)

    positive = clip_truncate(", ".join(parts), CLIP_SOFT_MAX)
    negative = (
        "cartoon, anime, blurry, deformed, extra faces, watermark, text, low quality"
    )
    return positive, negative
