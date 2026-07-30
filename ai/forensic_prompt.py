"""
Build a clean Stable Diffusion forensic-sketch prompt from an improved description.

Never send raw witness text directly — always engineer a structured prompt first.
Keeps prompts inside CLIP's ~77 token budget for SD 1.5.
"""

from __future__ import annotations

from utils.config import settings


def _clip_truncate(prompt: str, max_tokens: int = 70) -> str:
    tokens = prompt.split()
    if len(tokens) <= max_tokens:
        return prompt
    return " ".join(tokens[:max_tokens])


def build_forensic_prompt(improved_description: str) -> tuple[str, str]:
    """
    Convert improved description → SD prompt + negative prompt.

    Example style:
      "A realistic forensic facial sketch of a 30-year-old male with an oval face..."
    """
    subject = " ".join((improved_description or "").strip().rstrip(".").split())
    subject = subject[0].lower() + subject[1:] if subject else "a person"
    subject = _clip_truncate(subject, max_tokens=42)

    positive = _clip_truncate(
        f"A realistic forensic facial sketch of a {subject}, "
        "pencil sketch, front view, highly detailed forensic style, graphite on white paper",
        max_tokens=70,
    )
    negative = settings.negative_prompt
    return positive, negative


def build_face_seed_prompt(improved_description: str) -> tuple[str, str]:
    """Optional clear-face pass before pencil refine."""
    subject = " ".join((improved_description or "").strip().rstrip(".").split())
    subject = _clip_truncate(subject, max_tokens=45)
    positive = _clip_truncate(
        f"{subject}, front facing portrait, clear facial features, plain background",
        max_tokens=70,
    )
    return positive, settings.face_negative_prompt
