"""
Full / original structured prompt helper (Python).

Builds a longer field:value style prompt from structured_values
(for FLUX / SD3 — not CLIP-truncated).

Legacy WitnessProfile prompts remain in ai/prompt_builder.py (unchanged).
"""

from __future__ import annotations

from typing import Any

SKIP = frozenset({"none", "unknown", "not_available", ""})

GROUP_ORDER = (
    "age",
    "global",
    "face",
    "hair",
    "forehead",
    "brows",
    "eyes",
    "nose",
    "cheeks",
    "mouth",
    "jaw",
    "chin",
    "ears",
    "facial_hair",
    "skin",
    "marks",
    "accessories",
    "context",
    "holistic",
)


def generate_original_prompt(
    structured_values: dict[str, Any],
) -> tuple[str, str]:
    """Return (positive, negative) full prompt from structured_values."""
    lines: list[str] = []
    seen: set[str] = set()
    s = structured_values or {}

    for group in GROUP_ORDER:
        fields = s.get(group)
        if not isinstance(fields, dict):
            continue
        for field, value in fields.items():
            val = str(value).strip().replace("_", " ")
            if not val or val.lower() in SKIP:
                continue
            key = f"{group}.{field}"
            if key in seen:
                continue
            seen.add(key)
            lines.append(
                f"{group.replace('_', ' ')} {field.replace('_', ' ')}: {val}"
            )

    for group, fields in s.items():
        if group in GROUP_ORDER or not isinstance(fields, dict):
            continue
        for field, value in fields.items():
            val = str(value).strip().replace("_", " ")
            if not val or val.lower() in SKIP:
                continue
            key = f"{group}.{field}"
            if key in seen:
                continue
            seen.add(key)
            lines.append(
                f"{group.replace('_', ' ')} {field.replace('_', ' ')}: {val}"
            )

    positive = ", ".join(
        [
            "forensic facial composite portrait",
            "photorealistic face",
            "front-facing mugshot style",
            "neutral studio lighting",
            "high detail",
            "identity-focused",
            *lines,
        ]
    )
    negative = (
        "cartoon, anime, sketch lines only, blurry, low resolution, "
        "deformed face, extra limbs, watermark, text overlay, crowd, multiple faces"
    )
    return positive, negative
