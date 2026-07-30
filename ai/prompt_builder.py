"""
Convert a structured WitnessProfile into Stable Diffusion prompts.

Builds:
  - face_prompt      → txt2img (clear face)
  - sketch_prompt    → img2img refine (proper pencil composite)
"""

from __future__ import annotations

from utils.config import settings
from utils.profile import WitnessProfile


def _clean(value: str) -> str:
    return (value or "").strip()


def _is_set(value: str, blanks: tuple[str, ...] = ("", "Unknown", "Not specified", "None")) -> bool:
    text = _clean(value)
    return bool(text) and text.lower() not in {b.lower() for b in blanks}


def _age_short(age_range: str) -> str:
    text = _clean(age_range)
    if "(" in text and ")" in text:
        return text[text.find("(") + 1 : text.find(")")] + " year old"
    return text


def _clip_truncate(prompt: str, max_tokens: int = 72) -> str:
    tokens = prompt.split()
    if len(tokens) <= max_tokens:
        return prompt
    return " ".join(tokens[:max_tokens])


def _subject_parts(profile: WitnessProfile) -> list[str]:
    parts: list[str] = []

    gender = _clean(profile.gender).lower() if _is_set(profile.gender) else "person"
    if gender in {"non-binary / other", "unknown"}:
        gender = "person"
    parts.append(f"{_age_short(profile.age_range)} {gender}")

    if _is_set(profile.ethnicity):
        parts.append(_clean(profile.ethnicity).split("/")[0].strip().lower())

    if _is_set(profile.skin_tone):
        parts.append(f"{_clean(profile.skin_tone).lower()} skin")

    if _is_set(profile.face_shape):
        parts.append(f"{_clean(profile.face_shape).lower()} face")
    if _is_set(profile.jaw):
        parts.append(f"{_clean(profile.jaw).lower()} jaw")

    if profile.hair_color.lower() == "bald" or profile.hair_length.lower() == "bald":
        parts.append("bald")
    else:
        hair = " ".join(
            b
            for b in [
                _clean(profile.hair_length).lower(),
                _clean(profile.hair_style).lower(),
                _clean(profile.hair_color).lower(),
            ]
            if b and b != "unknown"
        )
        if hair:
            parts.append(f"{hair} hair")

    if _is_set(profile.facial_hair) and "none" not in profile.facial_hair.lower():
        parts.append(_clean(profile.facial_hair).lower())

    if _is_set(profile.eye_color):
        parts.append(f"{_clean(profile.eye_color).lower()} eyes")
    if _is_set(profile.eyebrows):
        parts.append(f"{_clean(profile.eyebrows).lower()} brows")

    if _is_set(profile.nose_shape):
        parts.append(f"{_clean(profile.nose_shape).lower()} nose")
    elif _is_set(profile.nose_size):
        parts.append(f"{_clean(profile.nose_size).lower()} nose")

    if _is_set(profile.lip_size):
        parts.append(f"{_clean(profile.lip_size).lower()} lips")

    for value in (profile.scars, profile.moles, profile.tattoos, profile.other_marks):
        if _clean(value):
            parts.append(_clean(value)[:48])

    if profile.accessories:
        parts.append("wearing " + " ".join(a.lower() for a in profile.accessories[:3]))

    if _clean(profile.additional_notes):
        parts.append(_clean(profile.additional_notes)[:50])

    return parts


def build_face_prompt(profile: WitnessProfile) -> tuple[str, str]:
    """Pass 1: clear face for structure (txt2img)."""
    subject = ", ".join(_subject_parts(profile))
    positive = _clip_truncate(f"{subject}, {settings.face_style_suffix}")
    return positive, settings.face_negative_prompt


def build_sketch_prompt(profile: WitnessProfile) -> tuple[str, str]:
    """Pass 2: pencil forensic composite (img2img refine)."""
    subject = ", ".join(_subject_parts(profile))
    positive = _clip_truncate(f"{settings.sketch_style_suffix}, {subject}")
    return positive, settings.negative_prompt


def build_prompt(profile: WitnessProfile) -> tuple[str, str]:
    """Default public API — returns the sketch-oriented prompt pair."""
    return build_sketch_prompt(profile)
