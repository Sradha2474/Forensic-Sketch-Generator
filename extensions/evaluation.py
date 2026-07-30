"""
Future: Quantitative evaluation (CLIP similarity, attribute accuracy, FID).

Score how well a generated sketch matches the witness profile / prompt.
"""

from __future__ import annotations

from typing import Any

from utils.profile import WitnessProfile


class SketchEvaluator:
    """Stub — not implemented in the 50% MVP."""

    def evaluate(self, image_path: str, profile: WitnessProfile) -> dict[str, Any]:
        raise NotImplementedError("Evaluation module is a post-MVP extension.")
