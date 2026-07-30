"""
Simple prompt UI — type a witness description, get a forensic pencil sketch.

Pipeline:
  User description → SD txt2img (face) → SD img2img (pencil) → dodge&burn polish
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from utils.config import settings

EXAMPLES = [
    "Male, about 35 years old, oval face, short black hair, thick eyebrows, brown eyes, medium nose, thin mustache, scar on left cheek",
    "Female, mid 20s, round face, long wavy brown hair, hazel eyes, small nose, full lips, wearing glasses",
    "Male, 40s, square jaw, bald, dark skin, deep-set eyes, broad nose, full beard, mole near right eye",
]


def _clip_truncate(text: str, max_tokens: int = 55) -> str:
    tokens = text.split()
    return " ".join(tokens[:max_tokens]) if len(tokens) > max_tokens else text


def build_prompts_from_description(description: str) -> tuple[str, str, str, str]:
    """Turn free text into face + sketch prompts (CLIP-safe length)."""
    subject = _clip_truncate(description.strip())

    face_prompt = _clip_truncate(
        f"{subject}, {settings.face_style_suffix}",
        max_tokens=72,
    )
    sketch_prompt = _clip_truncate(
        f"{settings.sketch_style_suffix}, {subject}",
        max_tokens=72,
    )
    return (
        face_prompt,
        settings.face_negative_prompt,
        sketch_prompt,
        settings.negative_prompt,
    )


def render_prompt_ui() -> str | None:
    """
    Simple write-a-description UI.
    Returns the description when Generate is clicked, else None.
    """
    st.markdown("### Describe the suspect")
    st.caption("Write a witness-style description. The system turns it into a graphite pencil forensic sketch.")

    if "description_text" not in st.session_state:
        st.session_state["description_text"] = EXAMPLES[0]

    example = st.selectbox("Quick examples", ["(custom)"] + EXAMPLES, index=1)
    if example != "(custom)" and st.button("Use this example", width="stretch"):
        st.session_state["description_text"] = example
        st.rerun()

    description = st.text_area(
        "Witness description / prompt",
        key="description_text",
        height=160,
        placeholder="e.g. Male, 30s, oval face, short black hair, brown eyes, scar on cheek…",
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        generate = st.button("Generate pencil sketch", type="primary", width="stretch")
    with c2:
        clear = st.button("Clear", width="stretch")

    if clear:
        st.session_state["description_text"] = ""
        st.session_state.pop("last_result", None)
        st.rerun()

    if generate:
        if not description.strip():
            st.warning("Please write a description first.")
            return None
        return description.strip()
    return None


def make_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
