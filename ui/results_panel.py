"""
Results panel: witness profile JSON, generated prompt, sketch, download.
"""

from __future__ import annotations

import io
from pathlib import Path

import streamlit as st

from utils.profile import WitnessProfile, profile_to_json


def render_results(
    profile: WitnessProfile,
    prompt: str,
    negative_prompt: str,
    sketch_image,
    sketch_path: Path | None = None,
    profile_path: Path | None = None,
    face_image=None,
    face_path: Path | None = None,
    sd_sketch_image=None,
    face_prompt: str | None = None,
) -> None:
    """Display MVP outputs after a successful generation."""
    demo = profile.to_dict()["demographics"]
    face = profile.to_dict()["face"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Gender", demo["gender"])
    c2.metric("Age", demo["age_range"].split("(")[0].strip())
    c3.metric("Face", face["shape"])

    tab_sketch, tab_pipeline, tab_profile, tab_prompt = st.tabs(
        ["Pencil sketch", "Pipeline stages", "Witness profile", "Prompts"]
    )

    with tab_sketch:
        st.image(sketch_image, caption="Graphite forensic pencil composite", width="stretch")
        if sketch_path:
            st.caption(f"Saved to `{sketch_path}`")

        buf = io.BytesIO()
        sketch_image.save(buf, format="PNG")
        st.download_button(
            label="Download sketch (PNG)",
            data=buf.getvalue(),
            file_name=f"forensic_sketch_{profile.profile_id}.png",
            mime="image/png",
            width="stretch",
        )

    with tab_pipeline:
        cols = st.columns(3)
        with cols[0]:
            st.caption("1 · SD face (txt2img)")
            if face_image is not None:
                st.image(face_image, width="stretch")
            else:
                st.info("N/A")
        with cols[1]:
            st.caption("2 · Pencil refine (img2img)")
            if sd_sketch_image is not None:
                st.image(sd_sketch_image, width="stretch")
            elif face_image is not None:
                st.image(face_image, width="stretch")
            else:
                st.info("N/A")
        with cols[2]:
            st.caption("3 · Dodge & burn polish")
            st.image(sketch_image, width="stretch")
        if face_path:
            st.caption(f"Raw face: `{face_path}`")

    with tab_profile:
        st.json(profile.to_dict())
        json_bytes = profile_to_json(profile).encode("utf-8")
        st.download_button(
            label="Download profile (JSON)",
            data=json_bytes,
            file_name=f"profile_{profile.profile_id}.json",
            mime="application/json",
            width="stretch",
        )
        if profile_path:
            st.caption(f"Saved to `{profile_path}`")

    with tab_prompt:
        if face_prompt:
            st.markdown("**Face prompt (txt2img)**")
            st.code(face_prompt, language=None)
        st.markdown("**Sketch prompt (img2img)**")
        st.code(prompt, language=None)
        st.markdown("**Negative prompt**")
        st.code(negative_prompt, language=None)
