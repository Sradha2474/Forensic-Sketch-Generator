"""
Stable Diffusion generation — STAAR-aligned two-pass sketch pipeline.

Pass 1: txt2img  → clear face (facial architecture)
Pass 2: img2img  → graphite pencil forensic composite (proper pencil look)

Extension point: swap in a LoRA-finetuned sketch checkpoint when available.
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


class ImageGenerator:
    """Lazy-loaded Stable Diffusion txt2img + img2img generator."""

    def __init__(
        self,
        model_id: str | None = None,
        device: str | None = None,
        cache_dir: str | None = None,
    ):
        self.model_id = model_id or settings.model_id
        self.cache_dir = cache_dir or settings.cache_dir
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._pipe = None
        self._img2img = None

    @property
    def is_loaded(self) -> bool:
        return self._pipe is not None

    def load(self) -> None:
        """Load txt2img and reuse weights for img2img."""
        if self._pipe is not None:
            return

        from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionPipeline

        logger.info("Loading Stable Diffusion model %s on %s", self.model_id, self.device)
        dtype = torch.float16 if self.device == "cuda" else torch.float32

        self._pipe = StableDiffusionPipeline.from_pretrained(
            self.model_id,
            torch_dtype=dtype,
            cache_dir=self.cache_dir,
            safety_checker=None,
            requires_safety_checker=False,
        )
        self._pipe = self._pipe.to(self.device)

        # Share UNet/VAE/text encoder — no second model download
        self._img2img = StableDiffusionImg2ImgPipeline(
            vae=self._pipe.vae,
            text_encoder=self._pipe.text_encoder,
            tokenizer=self._pipe.tokenizer,
            unet=self._pipe.unet,
            scheduler=self._pipe.scheduler,
            safety_checker=None,
            feature_extractor=getattr(self._pipe, "feature_extractor", None),
            requires_safety_checker=False,
        )
        self._img2img = self._img2img.to(self.device)

        try:
            self._pipe.enable_attention_slicing()
            self._img2img.enable_attention_slicing()
        except Exception:
            pass

        logger.info("txt2img + img2img pipelines ready")

    def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        num_inference_steps: int | None = None,
        guidance_scale: float | None = None,
    ) -> Image.Image:
        """Pass 1 — txt2img face synthesis."""
        if self._pipe is None:
            self.load()

        seed = settings.seed if seed is None else seed
        steps = num_inference_steps or settings.face_inference_steps
        guidance = guidance_scale or settings.face_guidance_scale
        neg = negative_prompt if negative_prompt is not None else settings.face_negative_prompt
        generator = torch.Generator(device=self.device).manual_seed(seed)

        result = self._pipe(
            prompt=prompt,
            negative_prompt=neg,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=settings.image_width,
            height=settings.image_height,
            generator=generator,
        )
        return result.images[0]

    def refine_as_pencil_sketch(
        self,
        image: Image.Image,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        strength: float | None = None,
        num_inference_steps: int | None = None,
        guidance_scale: float | None = None,
    ) -> Image.Image:
        """
        Pass 2 — img2img restyle into a proper graphite pencil sketch.

        This is the MVP stand-in for a LoRA-finetuned forensic sketch model
        (as described in STAAR / VisionMorph-style architectures).
        """
        if self._img2img is None:
            self.load()

        seed = settings.seed if seed is None else seed
        steps = num_inference_steps or getattr(settings, "refine_inference_steps", 28)
        guidance = guidance_scale or getattr(settings, "refine_guidance_scale", 8.0)
        strength = getattr(settings, "refine_strength", 0.58) if strength is None else strength
        neg = negative_prompt if negative_prompt is not None else settings.negative_prompt
        generator = torch.Generator(device=self.device).manual_seed(seed + 7)

        init = image.convert("RGB").resize(
            (settings.image_width, settings.image_height),
            Image.Resampling.LANCZOS,
        )

        result = self._img2img(
            prompt=prompt,
            negative_prompt=neg,
            image=init,
            strength=float(strength),
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        )
        return result.images[0]

    def generate_forensic_sketch(
        self,
        face_prompt: str,
        sketch_prompt: str,
        face_negative: str | None = None,
        sketch_negative: str | None = None,
        seed: int | None = None,
        enable_refine: bool | None = None,
    ) -> tuple[Image.Image, Image.Image]:
        """
        Full generative path.

        Returns (raw_face, pencil_sketch_from_sd).
        """
        face = self.generate(
            face_prompt,
            negative_prompt=face_negative,
            seed=seed,
        )
        do_refine = settings.enable_sketch_refine if enable_refine is None else enable_refine
        if not do_refine:
            return face, face

        sketch = self.refine_as_pencil_sketch(
            face,
            prompt=sketch_prompt,
            negative_prompt=sketch_negative,
            seed=seed,
        )
        return face, sketch

    def save(self, image: Image.Image, prefix: str = "face", directory: Path | None = None) -> Path:
        out_dir = Path(directory or settings.outputs_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if (prefix.startswith("face_") or prefix.startswith("sketch_")) and prefix.count("_") >= 2:
            filename = f"{prefix}.png"
        else:
            filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = out_dir / filename
        image.save(path)
        return path


_generator: Optional[ImageGenerator] = None


def get_generator() -> ImageGenerator:
    global _generator
    if _generator is None:
        _generator = ImageGenerator()
    return _generator
