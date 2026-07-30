"""
Legacy structured interview form (optional / unused by the prompt MVP UI).

Kept as an extension point. The live app uses app.py + styles + AI suggest flow.
"""

from __future__ import annotations

from utils.profile import WitnessProfile


def render_interview_form() -> WitnessProfile | None:
    """Deprecated in the prompt-based MVP — returns None."""
    import streamlit as st

    st.info(
        "Structured interview form is disabled in this MVP demo. "
        "Use the witness description box instead."
    )
    return None
