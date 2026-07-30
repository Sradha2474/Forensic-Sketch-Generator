"""
Future: Criminal / mugshot database search.

Given a forensic sketch, retrieve nearest neighbors from an enrolled gallery
(face embeddings + ranking UI).
"""

from __future__ import annotations

from typing import Any

from PIL import Image


class DatabaseSearch:
    """Stub — not implemented in the 50% MVP."""

    def search(self, sketch: Image.Image, top_k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError("Database search is a post-MVP extension.")
