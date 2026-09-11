"""MVP configuration — keep knobs in one place for easy tuning."""

from dataclasses import dataclass, field
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = ROOT_DIR / "outputs"
MODEL_CACHE_DIR = ROOT_DIR / "model_cache"


@dataclass
class Settings:
    """Runtime settings aligned with STAAR-style MVP architecture."""

    # Stable Diffusion base
    model_id: str = "runwayml/stable-diffusion-v1-5"
    cache_dir: str = str(MODEL_CACHE_DIR)
    image_width: int = 512
    image_height: int = 512
    seed: int = 42

    # Pass 1 — clear face synthesis (txt2img)
    face_inference_steps: int = 28
    face_guidance_scale: float = 7.5

    # Pass 2 — pencil sketch refinement (img2img) — critical for proper graphite look
    enable_sketch_refine: bool = True
    refine_inference_steps: int = 28
    refine_guidance_scale: float = 8.0
    refine_strength: float = 0.58  # 0.45–0.65: higher = more sketch-like, less photo

    # Legacy aliases used by older callers
    num_inference_steps: int = 28
    guidance_scale: float = 7.5

    # Pass 3 — classic OpenCV polish (report Phase 4: dodge & burn + edges)
    sketch_polish: bool = True
    sketch_sigma: float = 11.0  # Gaussian sigma for soft graphite strokes
    sketch_edge_blend: float = 0.12  # light Laplacian overlay (keep low)

    # Paths
    outputs_dir: Path = field(default_factory=lambda: OUTPUTS_DIR)

    # FLUX.1-schnell (RTX 4060 8GB defaults)
    flux_model_id: str = "black-forest-labs/FLUX.1-schnell"
    flux_steps: int = 4
    flux_guidance: float = 0.0
    flux_max_sequence_length: int = 256
    flux_width: int = 512
    flux_height: int = 512
    flux_cpu_offload: bool = True  # required on 8GB VRAM

    # Face pass style (keep short for CLIP 77 tokens)
    face_style_suffix: str = (
        "front facing portrait photo, clear facial features, studio lighting, plain background"
    )

    # Sketch refine style — forces graphite pencil composite look
    sketch_style_suffix: str = (
        "hand-drawn graphite pencil forensic composite sketch on white paper, "
        "soft shading, detailed eyes nose lips, clean pencil strokes"
    )

    # Backward-compatible alias used by prompt_builder
    style_suffix: str = (
        "hand-drawn graphite pencil forensic composite sketch on white paper, "
        "soft shading, detailed eyes nose lips, clean pencil strokes"
    )

    negative_prompt: str = (
        "blurry, noisy, grain, crosshatch mesh, canvas texture, stipple, "
        "cartoon, anime, colorful, photorealistic color photo, 3d render, "
        "deformed, watermark, text, low contrast, jpeg artifacts"
    )

    face_negative_prompt: str = (
        "blurry, deformed, cartoon, anime, multiple faces, watermark, text, low quality"
    )


settings = Settings()
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
