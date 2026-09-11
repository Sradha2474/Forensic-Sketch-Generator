"""
Model router — pick prompt style + which image generator backend.

Aligned with forenisic/lib/prompts/prompt_router.ts:

  sd15 / sd15_controlnet / sdxl  → micro prompt  → SD 1.5 generator
  flux / sd3                     → full prompt   → FLUX (sd3 later)
"""

from __future__ import annotations

from typing import Any, Literal

from ai.micro_prompt_builder import generate_micro_prompt
from ai.structured_full_prompt import generate_original_prompt

PromptMode = Literal["micro", "original"]
BackendId = Literal["sd15", "flux", "unsupported"]

MICRO_MODELS = frozenset({"sd15", "sd15_controlnet", "sdxl"})
FULL_MODELS = frozenset({"flux", "sd3"})


def prompt_mode_for_model(model: str) -> PromptMode:
    m = (model or "sd15").strip().lower()
    if m in FULL_MODELS:
        return "original"
    return "micro"


def backend_for_model(model: str) -> BackendId:
    m = (model or "sd15").strip().lower()
    if m in ("sd15", "sd15_controlnet"):
        return "sd15"
    if m == "flux":
        return "flux"
    # sdxl / sd3 not wired yet
    return "unsupported"


def build_prompts_for_model(
    structured_values: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    """
    Route structured profile → micro or full prompt pair.
    """
    mode = prompt_mode_for_model(model)
    if mode == "micro":
        positive, negative = generate_micro_prompt(structured_values)
    else:
        positive, negative = generate_original_prompt(structured_values)

    return {
        "model": (model or "sd15").strip().lower(),
        "mode": mode,
        "backend": backend_for_model(model),
        "positive": positive,
        "negative": negative,
    }
