"""
AI-Assisted Forensic Sketch Generator — polished MVP demo UI.

Flow:
  Witness text → AI improve description → forensic prompt → SD sketch → download
"""

from __future__ import annotations

import io
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.description_enhancer import enhance_description
from ai.forensic_prompt import build_face_seed_prompt, build_forensic_prompt
from ai.image_generator import get_generator
from ai.sketch_processor import apply_pencil_sketch, save_sketch
from ui.styles import empty_preview, inject_theme, render_navbar
from utils.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLACEHOLDER = (
    "Example:\n"
    "Male, around 30 years old, oval face, medium brown skin, short black curly hair, "
    "thick eyebrows, sharp jawline, straight nose, thin lips, wearing rectangular glasses..."
)


@st.cache_resource(show_spinner=False)
def _cached_generator():
    gen = get_generator()
    gen.load()
    return gen


def _init_state() -> None:
    defaults = {
        "witness_raw": "",
        "improved_description": "",
        "show_improved": False,
        "last_result": None,
        "gen_status": "Idle",
        "do_generate": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _sidebar() -> None:
    with st.sidebar:
        st.markdown("### Controls")
        st.session_state["enable_refine"] = st.toggle(
            "Pencil refine (img2img)",
            value=True,
            help="Recommended for a proper graphite forensic look.",
        )
        st.session_state["refine_strength"] = st.slider(
            "Pencil strength",
            min_value=0.40,
            max_value=0.75,
            value=0.58,
            step=0.01,
        )
        st.session_state["enable_polish"] = st.toggle("Dodge & burn polish", value=True)
        st.caption("Educational / research demo only.")


def _render_left() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-kicker">✦ Witness intake</div>', unsafe_allow_html=True)
    st.markdown(
        '<h1 class="panel-title">AI-Assisted Forensic Sketch Generator</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="panel-sub">Describe the suspect in as much detail as possible. '
        "The AI will analyze your description and generate a forensic sketch.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="step-row">
  <div class="step-chip"><b>1</b> Describe</div>
  <div class="step-chip"><b>2</b> AI improve</div>
  <div class="step-chip"><b>3</b> Generate</div>
  <div class="step-chip"><b>4</b> Download</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Witness description</div>', unsafe_allow_html=True)
    st.text_area(
        "Witness description",
        key="witness_raw",
        height=180,
        placeholder=PLACEHOLDER,
        label_visibility="collapsed",
    )

    c1, c2 = st.columns(2)
    with c1:
        voice = st.button("🎤 Voice Input", width="stretch")
    with c2:
        suggest = st.button("✨ AI Suggest Description", width="stretch")

    if voice:
        st.info("Voice input coming soon — paste or type the description for now.")

    if suggest:
        raw = (st.session_state.get("witness_raw") or "").strip()
        if not raw:
            st.warning("Write a short description first (e.g. “Man with beard.”).")
        else:
            improved = enhance_description(raw)
            st.session_state["improved_description"] = improved
            st.session_state["show_improved"] = True
            st.toast("Description improved — review and edit below.")

    if st.session_state.get("show_improved") or st.session_state.get("improved_description"):
        st.markdown(
            '<div class="section-label">Improved description (editable)</div>',
            unsafe_allow_html=True,
        )
        st.text_area(
            "Improved description",
            key="improved_description",
            height=140,
            label_visibility="collapsed",
        )

    st.markdown('<div style="height:0.55rem"></div>', unsafe_allow_html=True)
    generate = st.button("🎨 Generate Sketch", type="primary", width="stretch")
    if generate:
        improved = (st.session_state.get("improved_description") or "").strip()
        raw = (st.session_state.get("witness_raw") or "").strip()
        if not improved and not raw:
            st.warning("Please enter a witness description first.")
        else:
            if not improved:
                improved = enhance_description(raw)
                st.session_state["improved_description"] = improved
                st.session_state["show_improved"] = True
            st.session_state["do_generate"] = True

    st.markdown(
        """
<div class="tip-row">
  <div class="tip">Include age + face shape</div>
  <div class="tip">Hair · eyes · nose</div>
  <div class="tip">Scars / glasses help</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_right() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-kicker">✦ Sketchboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Generated output</div>', unsafe_allow_html=True)

    result = st.session_state.get("last_result")
    if not result:
        empty_preview()
        st.markdown(
            f'<div style="margin-top:1rem;color:#9aa3bf;font-size:0.85rem;">'
            f'Status: <span class="status-pill"><span class="dot"></span>'
            f'{st.session_state.get("gen_status", "Idle")}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown(
        f'<div class="status-pill"><span class="dot"></span> {result.get("status", "Complete")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-label" style="margin-top:0.95rem;">Generated image</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="image-frame">', unsafe_allow_html=True)
    st.image(result["sketch"], width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-label">Prompt used</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="prompt-box">{result["prompt"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Improved description</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="prompt-box">{result["improved"]}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:0.45rem"></div>', unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        buf = io.BytesIO()
        result["sketch"].save(buf, format="PNG")
        st.download_button(
            "⬇ Download",
            data=buf.getvalue(),
            file_name=f"forensic_sketch_{result['run_id']}.png",
            mime="image/png",
            width="stretch",
        )
    with b2:
        again = st.button("🔄 Generate Again", width="stretch")
        if again:
            st.session_state["do_generate"] = True
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _run_generation() -> None:
    improved = (st.session_state.get("improved_description") or "").strip()
    if not improved:
        raw = (st.session_state.get("witness_raw") or "").strip()
        improved = enhance_description(raw)
        st.session_state["improved_description"] = improved

    # Never send raw witness text — engineer prompt from improved description
    face_prompt, face_neg = build_face_seed_prompt(improved)
    sketch_prompt, sketch_neg = build_forensic_prompt(improved)

    enable_refine = st.session_state.get("enable_refine", True)
    refine_strength = float(st.session_state.get("refine_strength", 0.58))
    enable_polish = st.session_state.get("enable_polish", True)
    settings.sketch_polish = enable_polish

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    badge = "Loading"
    render_navbar(badge=f"{badge} Screen")

    status = st.status("Working…", expanded=True)
    try:
        status.update(label="Analyzing witness description...", state="running")
        status.write("Analyzing witness description...")

        status.write("Extracting facial attributes...")
        status.update(label="Extracting facial attributes...", state="running")

        status.write("Loading Stable Diffusion…")
        generator = _cached_generator()

        status.write("Generating forensic sketch...")
        status.update(label="Generating forensic sketch...", state="running")
        face = generator.generate(face_prompt, negative_prompt=face_neg)

        if enable_refine:
            sd_sketch = generator.refine_as_pencil_sketch(
                face,
                prompt=sketch_prompt,
                negative_prompt=sketch_neg,
                strength=refine_strength,
            )
        else:
            # Direct sketch prompt generation as fallback
            sd_sketch = generator.generate(sketch_prompt, negative_prompt=sketch_neg)

        status.write("Finalizing image...")
        status.update(label="Finalizing image...", state="running")
        sketch = apply_pencil_sketch(sd_sketch) if enable_polish else sd_sketch
        sketch_path = save_sketch(sketch, prefix=f"sketch_{run_id}")

        status.update(label="Sketch ready", state="complete")
        st.session_state["gen_status"] = "Complete"
        st.session_state["last_result"] = {
            "run_id": run_id,
            "improved": improved,
            "prompt": sketch_prompt,
            "face_prompt": face_prompt,
            "face": face,
            "sd_sketch": sd_sketch,
            "sketch": sketch,
            "sketch_path": str(sketch_path),
            "status": "Generation complete",
        }
    except Exception as exc:
        logger.exception("Generation failed")
        status.update(label="Generation failed", state="error")
        st.session_state["gen_status"] = "Error"
        st.error(f"Generation failed: {exc}")
    finally:
        st.session_state["do_generate"] = False


def main() -> None:
    st.set_page_config(
        page_title="AI Forensic Sketch Generator",
        page_icon="🕵️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_theme()
    _init_state()
    _sidebar()

    if st.session_state.get("do_generate"):
        render_navbar(badge="Loading Screen")
        _run_generation()
        st.rerun()

    render_navbar(badge="MVP Demo")
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        _render_left()
    with right:
        _render_right()


if __name__ == "__main__":
    main()
