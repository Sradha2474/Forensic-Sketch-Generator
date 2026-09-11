"""
FLUX.1-schnell generator — separate from SD 1.5 ImageGenerator.

Tuned for RTX 4060 8GB: float16 + model CPU offload + VAE slicing/tiling + 512px.
Do NOT load at API startup — lazy-load on first model=flux request.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

from utils.config import settings

logger = logging.getLogger(__name__)


class FluxGenerator:
    """Lazy-loaded FLUX.1-schnell txt2img (full-prompt path)."""

    def __init__(
        self,
        model_id: str | None = None,
        device: str | None = None,
        cache_dir: str | None = None,
    ):
        self.model_id = model_id or settings.flux_model_id
        self.cache_dir = cache_dir or settings.cache_dir
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._pipe = None

    @property
    def is_loaded(self) -> bool:
        return self._pipe is not None

    def load(self) -> None:
        """Load FluxPipeline once (large download on first call)."""
        if self._pipe is not None:
            return

        from diffusers import FluxPipeline

        logger.info(
            "Loading FLUX model %s (device=%s, offload=%s) — first run downloads to cache",
            self.model_id,
            self.device,
            settings.flux_cpu_offload,
        )

        dtype = torch.float16 if self.device == "cuda" else torch.float32

        self._pipe = FluxPipeline.from_pretrained(
            self.model_id,
            torch_dtype=dtype,
            cache_dir=self.cache_dir,
        )

        if self.device == "cuda" and settings.flux_cpu_offload:
            # 8GB VRAM: keep most weights on CPU, stream to GPU during denoise
            self._pipe.enable_model_cpu_offload()
        elif self.device == "cuda":
            self._pipe = self._pipe.to("cuda")
        else:
            self._pipe = self._pipe.to("cpu")
            logger.warning(
                "FLUX on CPU will be extremely slow — CUDA GPU strongly recommended"
            )

        try:
            self._pipe.vae.enable_slicing()
            self._pipe.vae.enable_tiling()
        except Exception:
            pass

        logger.info("FLUX pipeline ready: %s", self.model_id)

    def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        num_inference_steps: int | None = None,
        guidance_scale: float | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> Image.Image:
        """
        Generate a face from a full (non-CLIP-truncated) prompt.

        FLUX.1-schnell: guidance_scale=0, ~4 steps.
        negative_prompt is accepted for API symmetry but schnell typically ignores it.
        """
        if self._pipe is None:
            self.load()

        seed = settings.seed if seed is None else int(seed)
        steps = num_inference_steps if num_inference_steps is not None else settings.flux_steps
        guidance = (
            guidance_scale if guidance_scale is not None else settings.flux_guidance
        )
        w = width or settings.flux_width
        h = height or settings.flux_height

        # Generator on CPU is safest with cpu_offload; CUDA generator when fully on GPU
        gen_device = "cpu" if settings.flux_cpu_offload or self.device == "cpu" else self.device
        generator = torch.Generator(device=gen_device).manual_seed(seed)

        logger.info(
            "FLUX generate steps=%s guidance=%s size=%sx%s seed=%s prompt_chars=%s",
            steps,
            guidance,
            w,
            h,
            seed,
            len(prompt),
        )

        # negative_prompt unused by schnell; keep kwargs clean
        _ = negative_prompt

        result = self._pipe(
            prompt=prompt,
            guidance_scale=float(guidance),
            num_inference_steps=int(steps),
            max_sequence_length=settings.flux_max_sequence_length,
            width=int(w),
            height=int(h),
            generator=generator,
        )
        return result.images[0]

    def generate_forensic_face(
        self,
        prompt: str,
        seed: int | None = None,
    ) -> Image.Image:
        """Face pass with a light forensic portrait cue (full prompt retained)."""
        p = prompt.strip()
        style = (
            "front-facing forensic facial composite portrait, "
            "clear identity features, neutral studio lighting"
        )
        if "forensic" not in p.lower() and "portrait" not in p.lower():
            p = f"{style}. {p}"
        return self.generate(prompt=p, seed=seed)

    def save(
        self,
        image: Image.Image,
        prefix: str = "flux",
        directory: Path | None = None,
    ) -> Path:
        out_dir = Path(directory or settings.outputs_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = out_dir / filename
        image.save(path)
        return path


_flux_generator: Optional[FluxGenerator] = None


def get_flux_generator() -> FluxGenerator:
    global _flux_generator
    if _flux_generator is None:
        _flux_generator = FluxGenerator()
    return _flux_generator
