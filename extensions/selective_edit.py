"""
Future: Selective region editing (inpaint / ControlNet).

Allow an investigator to revise nose, eyes, hair, etc. without regenerating
the whole face. Hook after the initial sketch is shown in the UI.
"""

from __future__ import annotations

from typing import Any

from PIL import Image


class SelectiveEditor:
    """Stub — not implemented in the 50% MVP."""

    def edit_region(
        self,
        image: Image.Image,
        region: str,
        new_attributes: dict[str, Any],
    ) -> Image.Image:
        raise NotImplementedError("Selective editing is a post-MVP extension.")
