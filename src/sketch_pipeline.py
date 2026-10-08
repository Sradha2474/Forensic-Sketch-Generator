# src/sketch_pipeline.py
# ---------------------------------------------------------------
# Core generation pipeline: baseline Stable Diffusion, ControlNet
# self-refine pass, optional LoRA sketch-style, and long-prompt
# handling via compel (bypasses CLIP's 77-token truncation).
#
# Used by:
#   - scripts/colab_server.py  (exposes this over an API from Colab's GPU)
#   - app.py                   (Streamlit "Compare Methods" mode)
#   - generate.py stays separate as the original baseline entry point
#
# Config (model IDs, LoRA repo, etc.) is loaded from config/sketch_config.yaml
# instead of being hardcoded here, so you can swap models without touching code.
# ---------------------------------------------------------------

import os
import yaml
import cv2
import torch
import numpy as np
from PIL import Image

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionControlNetPipeline,
    ControlNetModel,
    UniPCMultistepScheduler,
)
from compel import Compel

# --- Config -------------------------------------------------------

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "sketch_config.yaml"
)

def load_config(path: str = _CONFIG_PATH) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

CONFIG = load_config()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

QUALITY_TAGS = CONFIG["prompt"]["quality_tags"]
NEGATIVE_PROMPT = CONFIG["prompt"]["negative_prompt"]

# --- Model loading (lazy singletons — only load once per process) --

_base_pipe = None
_refine_pipe = None

def get_base_pipe() -> StableDiffusionPipeline:
    global _base_pipe
    if _base_pipe is None:
        _base_pipe = StableDiffusionPipeline.from_pretrained(
            CONFIG["models"]["base_model"], torch_dtype=DTYPE, safety_checker=None
        ).to(DEVICE)
        _base_pipe.scheduler = UniPCMultistepScheduler.from_config(
            _base_pipe.scheduler.config
        )
    return _base_pipe

def get_refine_pipe() -> StableDiffusionControlNetPipeline:
    global _refine_pipe
    if _refine_pipe is None:
        controlnet = ControlNetModel.from_pretrained(
            CONFIG["models"]["controlnet_model"], torch_dtype=DTYPE
        )
        _refine_pipe = StableDiffusionControlNetPipeline.from_pretrained(
            CONFIG["models"]["base_model"],
            controlnet=controlnet,
            torch_dtype=DTYPE,
            safety_checker=None,
        ).to(DEVICE)
        _refine_pipe.scheduler = UniPCMultistepScheduler.from_config(
            _refine_pipe.scheduler.config
        )
        if CONFIG["lora"]["enabled"]:
            _refine_pipe.load_lora_weights(CONFIG["lora"]["repo_id"])
            _refine_pipe.fuse_lora(lora_scale=CONFIG["lora"]["scale"])
    return _refine_pipe

# --- Prompt handling ------------------------------------------------

def build_prompt(witness_description: str) -> str:
    """Wraps the raw witness description with structure + quality tags.

    NOTE: Order features with the most distinctive/identifying details
    first (scars, unusual marks, striking asymmetries) — CLIP attends
    more strongly to earlier tokens, and this mirrors how a real
    cognitive interview elicits the most vivid details first anyway.
    """
    desc = witness_description.strip().rstrip(".")
    return f"{desc}, {QUALITY_TAGS}"

def get_long_prompt_embeddings(pipe, prompt: str, negative_prompt: str):
    """Encodes prompts of any length, bypassing CLIP's 77-token hard
    truncation by chunking into multiple windows and concatenating
    embeddings (via compel)."""
    compel_proc = Compel(tokenizer=pipe.tokenizer, text_encoder=pipe.text_encoder)
    prompt_embeds = compel_proc.build_conditioning_tensor(prompt)
    negative_embeds = compel_proc.build_conditioning_tensor(negative_prompt)
    [prompt_embeds, negative_embeds] = compel_proc.pad_conditioning_tensors_to_same_length(
        [prompt_embeds, negative_embeds]
    )
    return prompt_embeds, negative_embeds

# --- Image helpers ---------------------------------------------------

def to_canny(image: Image.Image, low: int = 100, high: int = 200) -> Image.Image:
    arr = np.array(image.convert("RGB"))
    edges = cv2.Canny(arr, low, high)
    return Image.fromarray(np.stack([edges] * 3, axis=-1))

# --- Generation stages ------------------------------------------------

def generate_baseline(witness_description: str, seed: int = 42) -> Image.Image:
    """Stage A: plain Stable Diffusion, same as generate.py's original
    approach but with the improved prompt + no-truncation embeddings."""
    pipe = get_base_pipe()
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    prompt_embeds, negative_embeds = get_long_prompt_embeddings(
        pipe, build_prompt(witness_description), NEGATIVE_PROMPT
    )
    image = pipe(
        prompt_embeds=prompt_embeds,
        negative_prompt_embeds=negative_embeds,
        num_inference_steps=CONFIG["generation"]["num_inference_steps"],
        guidance_scale=CONFIG["generation"]["guidance_scale"],
        generator=generator,
    ).images[0]
    return image

def generate_refined(
    witness_description: str,
    seed: int = 42,
    controlnet_conditioning_scale: float = None,
) -> tuple[Image.Image, Image.Image, Image.Image]:
    """Stage B: self-refine pass. Generates a baseline image, extracts
    Canny edges from it, then runs a ControlNet(+LoRA) pass conditioned
    on those edges to lock structure while improving style/detail.

    Returns (baseline_image, canny_edges, refined_image) so all three
    can be logged side by side for ablation figures.
    """
    if controlnet_conditioning_scale is None:
        controlnet_conditioning_scale = CONFIG["generation"]["controlnet_conditioning_scale"]

    baseline_img = generate_baseline(witness_description, seed=seed)
    canny_img = to_canny(baseline_img)

    pipe = get_refine_pipe()
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    prompt_embeds, negative_embeds = get_long_prompt_embeddings(
        pipe, build_prompt(witness_description), NEGATIVE_PROMPT
    )
    refined_img = pipe(
        prompt_embeds=prompt_embeds,
        negative_prompt_embeds=negative_embeds,
        image=canny_img,
        num_inference_steps=CONFIG["generation"]["num_inference_steps"],
        guidance_scale=CONFIG["generation"]["guidance_scale"],
        controlnet_conditioning_scale=controlnet_conditioning_scale,
        generator=generator,
    ).images[0]

    return baseline_img, canny_img, refined_img