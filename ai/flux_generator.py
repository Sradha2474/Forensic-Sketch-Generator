"""
FLUX.1-schnell generator — separate from SD 1.5 ImageGenerator.

Tuned for RTX 4060 8GB / 16GB RAM:
  - Prefer pre-quantized NF4 package (avoids on-the-fly 10GB shard conversion crash)
  - bf16 compute when possible; NF4 pkg commonly uses fp16 weights
  - model / sequential CPU offload (never .to("cuda") on BnB pipelines)
  - 512×512, 4 steps, guidance_scale=0, max_sequence_length≤256

Do NOT load at API startup by default — lazy-load, or set flux_warmup_on_startup /
run scripts/generate_flux_full_prompt.py to warm outside the HTTP request.

Auth:
  - Base model black-forest-labs/FLUX.1-schnell is gated (HF_TOKEN + license).
  - Pre-quantized NF4 package may still need HF_TOKEN for download rate limits.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

from utils.config import MODEL_CACHE_DIR, ROOT_DIR, settings

logger = logging.getLogger(__name__)

NF4_TRANSFORMER_DIR = MODEL_CACHE_DIR / "flux_nf4_transformer"


def _load_dotenv_files() -> None:
    """Load HF_TOKEN from common .env locations if not already set."""
    if os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        return
    for path in (
        ROOT_DIR / ".env",
        ROOT_DIR / "forenisic" / ".env",
    ):
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN") and v:
                    os.environ.setdefault(k, v)
        except OSError:
            continue


def _hf_token() -> str | None:
    _load_dotenv_files()
    return (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or None
    )


def _uses_offload() -> bool:
    mode = (settings.flux_offload_mode or "model").strip().lower()
    if mode in ("model", "sequential"):
        return True
    return bool(settings.flux_cpu_offload)


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
        self.loaded_from: str | None = None
        self._placement: str = "unloaded"

    @property
    def is_loaded(self) -> bool:
        return self._pipe is not None

    def unload(self) -> None:
        """Free Flux from VRAM/RAM so SD 1.5 can use the GPU."""
        if self._pipe is None:
            return
        logger.info("Unloading FLUX to free VRAM…")
        self._pipe = None
        self._placement = "unloaded"
        self.loaded_from = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        logger.info("FLUX unloaded")

    def _apply_vae_opts(self) -> None:
        try:
            self._pipe.vae.enable_slicing()
            self._pipe.vae.enable_tiling()
        except Exception:
            pass

    def _apply_offload(self) -> None:
        """
        Placement for non–device_map pipelines.

        NOTE (Windows + BnB NF4 pkg): enable_model_cpu_offload() hard-crashes
        with ACCESS_VIOLATION (0xC0000005). Prefer device_map='cuda' in
        _load_prequantized_nf4 instead.
        """
        offload_mode = (settings.flux_offload_mode or "model").strip().lower()
        if self.device == "cuda":
            if offload_mode == "sequential":
                self._pipe.enable_sequential_cpu_offload()
            elif offload_mode == "model":
                self._pipe.enable_model_cpu_offload()
            else:
                self._pipe = self._pipe.to("cuda")
        else:
            self._pipe = self._pipe.to("cpu")
            logger.warning("FLUX on CPU will be extremely slow")
        self._apply_vae_opts()

    def _load_prequantized_nf4(self, token: str | None) -> None:
        """Load already-NF4 weights with device_map=cuda (works on RTX 4060 8GB)."""
        from diffusers import FluxPipeline

        nf4_id = settings.flux_nf4_model_id
        # NF4 package is fp16; device_map=cuda avoids the Windows offload crash
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        logger.info(
            "Loading pre-quantized NF4 pipeline: %s (dtype=%s, device_map=cuda)",
            nf4_id,
            dtype,
        )

        kwargs = dict(
            torch_dtype=dtype,
            cache_dir=self.cache_dir,
            token=token,
        )
        if self.device == "cuda":
            kwargs["device_map"] = "cuda"

        self._pipe = FluxPipeline.from_pretrained(nf4_id, **kwargs)
        self.loaded_from = nf4_id
        self._placement = "device_map_cuda" if self.device == "cuda" else "cpu"
        self._apply_vae_opts()
        logger.info("Pre-quantized NF4 pipeline ready (placement=%s)", self._placement)

    def _load_onthefly_nf4(self, token: str | None) -> None:
        """
        Quantize while loading from the gated base repo.
        Peak RAM is high on Windows (often ACCESS_VIOLATION on 16GB) — prefer NF4 pkg.
        """
        from diffusers import (
            BitsAndBytesConfig as DiffusersBnb,
            FluxPipeline,
            FluxTransformer2DModel,
        )
        from huggingface_hub.errors import GatedRepoError, HfHubHTTPError
        from transformers import BitsAndBytesConfig as TransformersBnb
        from transformers import T5EncoderModel

        dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        common = dict(cache_dir=self.cache_dir, token=token)
        quant = (settings.flux_quant or "none").strip().lower()

        try:
            if (
                quant == "nf4"
                and self.device == "cuda"
                and NF4_TRANSFORMER_DIR.is_dir()
                and any(NF4_TRANSFORMER_DIR.iterdir())
            ):
                logger.info("Loading cached NF4 transformer from %s", NF4_TRANSFORMER_DIR)
                transformer = FluxTransformer2DModel.from_pretrained(
                    str(NF4_TRANSFORMER_DIR),
                    torch_dtype=dtype,
                    token=token,
                )
            else:
                transformer_kwargs = dict(
                    subfolder="transformer",
                    torch_dtype=dtype,
                    **common,
                )
                if quant == "nf4" and self.device == "cuda":
                    transformer_kwargs["quantization_config"] = DiffusersBnb(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=dtype,
                        bnb_4bit_use_double_quant=True,
                    )
                transformer = FluxTransformer2DModel.from_pretrained(
                    self.model_id, **transformer_kwargs
                )
                if quant == "nf4" and self.device == "cuda":
                    try:
                        NF4_TRANSFORMER_DIR.mkdir(parents=True, exist_ok=True)
                        transformer.save_pretrained(str(NF4_TRANSFORMER_DIR))
                        logger.info("Saved NF4 transformer cache → %s", NF4_TRANSFORMER_DIR)
                    except Exception as exc:
                        logger.warning("Could not cache NF4 transformer: %s", exc)

            logger.info("Transformer loaded")

            t5_kwargs = dict(subfolder="text_encoder_2", torch_dtype=dtype, **common)
            if settings.flux_quantize_t5 and self.device == "cuda":
                t5_kwargs["quantization_config"] = TransformersBnb(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=dtype,
                )
            text_encoder_2 = T5EncoderModel.from_pretrained(self.model_id, **t5_kwargs)
            logger.info("T5 loaded")

            self._pipe = FluxPipeline.from_pretrained(
                self.model_id,
                transformer=transformer,
                text_encoder_2=text_encoder_2,
                torch_dtype=dtype,
                **common,
            )
            self.loaded_from = self.model_id
        except (GatedRepoError, HfHubHTTPError) as exc:
            raise RuntimeError(
                "Cannot download FLUX.1-schnell (gated). Accept the license at "
                "https://huggingface.co/black-forest-labs/FLUX.1-schnell and set HF_TOKEN.\n"
                f"Original error: {exc}"
            ) from exc

    def _load_full_precision(self, token: str | None) -> None:
        from diffusers import FluxPipeline
        from huggingface_hub.errors import GatedRepoError, HfHubHTTPError

        dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        try:
            self._pipe = FluxPipeline.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
                cache_dir=self.cache_dir,
                token=token,
            )
            self.loaded_from = self.model_id
        except (GatedRepoError, HfHubHTTPError) as exc:
            raise RuntimeError(
                "Cannot download FLUX.1-schnell (gated). Accept the license at "
                "https://huggingface.co/black-forest-labs/FLUX.1-schnell and set HF_TOKEN.\n"
                f"Original error: {exc}"
            ) from exc

    def load(self) -> None:
        """Load FLUX with NF4 (+ CPU offload) for 8GB VRAM / 16GB RAM."""
        if self._pipe is not None:
            return

        token = _hf_token()
        quant = (settings.flux_quant or "none").strip().lower()
        offload_mode = (settings.flux_offload_mode or "model").strip().lower()

        logger.info(
            "Loading FLUX (quant=%s, t5_4bit=%s, offload=%s, base=%s, nf4_pkg=%s, hf_token=%s)",
            quant,
            settings.flux_quantize_t5,
            offload_mode,
            self.model_id,
            settings.flux_nf4_model_id,
            "yes" if token else "NO",
        )

        if quant == "nf4" and self.device == "cuda":
            try:
                self._load_prequantized_nf4(token)
            except Exception as exc:
                logger.exception(
                    "Pre-quantized NF4 package failed (%s). "
                    "Falling back to on-the-fly quant from %s — may crash on 16GB RAM.",
                    exc,
                    self.model_id,
                )
                self._load_onthefly_nf4(token)
                self._placement = "offload"
                self._apply_offload()
        elif quant == "nf4":
            logger.warning("NF4 requested but CUDA unavailable — loading full CPU pipeline")
            self._load_full_precision(token)
            self._placement = "cpu"
            self._apply_offload()
        else:
            self._load_full_precision(token)
            self._placement = "offload"
            self._apply_offload()

        logger.info(
            "FLUX pipeline ready (loaded_from=%s, device=%s, placement=%s)",
            self.loaded_from,
            self.device,
            self._placement,
        )

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

        FLUX.1-schnell: guidance_scale=0, ~4 steps, max_sequence_length≤256.
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
        seq_len = min(int(settings.flux_max_sequence_length), 256)

        # CPU generator is safest for device_map=cuda and offload paths
        generator = torch.Generator(device="cpu").manual_seed(seed)

        logger.info(
            "FLUX generate steps=%s guidance=%s size=%sx%s seed=%s seq=%s prompt_chars=%s",
            steps,
            guidance,
            w,
            h,
            seed,
            seq_len,
            len(prompt),
        )

        _ = negative_prompt

        pipe_kwargs = dict(
            prompt=prompt,
            guidance_scale=float(guidance),
            num_inference_steps=int(steps),
            max_sequence_length=seq_len,
            width=int(w),
            height=int(h),
            generator=generator,
        )

        try:
            result = self._pipe(**pipe_kwargs)
        except torch.cuda.OutOfMemoryError:
            # model/sequential offload crashes on Windows+BnB; retry at 512 if larger
            logger.warning("OOM during Flux generate — emptying cache and retrying 512²")
            torch.cuda.empty_cache()
            pipe_kwargs["width"] = 512
            pipe_kwargs["height"] = 512
            pipe_kwargs["generator"] = torch.Generator(device="cpu").manual_seed(seed)
            result = self._pipe(**pipe_kwargs)

        return result.images[0]

    def generate_forensic_face(
        self,
        prompt: str,
        seed: int | None = None,
    ) -> Image.Image:
        """Face pass steered toward graphite pencil forensic composite (full prompt kept)."""
        p = prompt.strip()
        sketch_style = (
            "hand-drawn graphite pencil forensic composite sketch on white paper, "
            "front-facing, soft shading, detailed eyes nose lips, clean pencil strokes, "
            "monochrome graphite, clear identity features, no color photo"
        )
        lower = p.lower()
        if "pencil" not in lower and "graphite" not in lower and "sketch" not in lower:
            p = f"{sketch_style}. {p}"
        elif "forensic" not in lower and "portrait" not in lower:
            p = f"{sketch_style}. {p}"
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
