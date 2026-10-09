"""
FastAPI image worker for Forensic Sketch Generator.

Routes:
  model=sd15  → ai.image_generator (SD 1.5 two-pass)  [lazy-load; unloads Flux]
  model=flux  → ai.flux_generator (FLUX.1-schnell NF4) [lazy-load; unloads SD]

Run from repo root:
  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.flux_generator import get_flux_generator
from ai.image_generator import get_generator
from ai.model_router import backend_for_model
from ai.sketch_processor import apply_pencil_sketch
from utils.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forensic.api")

# Serialize GPU work — SD and FLUX must not share the GPU concurrently
_gen_lock = asyncio.Lock()

SKETCH_SUFFIX = (
    ", hand-drawn graphite pencil forensic composite sketch on white paper, "
    "soft shading, detailed facial features, clean pencil strokes"
)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    label: str = "image"
    enable_refine: bool = True
    enable_polish: bool = True
    # sd15 (default) | flux
    model: Optional[str] = "sd15"


class GenerateResponse(BaseModel):
    label: str
    seed: int
    image_base64: str
    mime_type: str = "image/png"
    model: str = "sd15"


def _pil_to_b64(image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _with_sketch_style(prompt: str) -> str:
    p = prompt.strip()
    if "pencil" in p.lower() or "forensic" in p.lower():
        return p
    return p + SKETCH_SUFFIX


def _warmup_flux_background() -> None:
    """Load NF4 FLUX outside an HTTP request (avoids UI ECONNRESET on first use)."""
    try:
        logger.info("Background FLUX warm-up starting…")
        flux = get_flux_generator()
        flux.load()
        logger.info("Background FLUX warm-up complete (flux_loaded=True)")
    except Exception:
        logger.exception("Background FLUX warm-up failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do NOT preload SD on 8GB VRAM — SD and Flux cannot share the GPU.
    # Each model lazy-loads on first request; the other is unloaded first.
    torch = __import__("torch")
    logger.info(
        "API ready (lazy SD + Flux). cuda=%s — models load on first /generate",
        torch.cuda.is_available(),
    )
    if settings.flux_warmup_on_startup:
        asyncio.get_running_loop().run_in_executor(None, _warmup_flux_background)
    yield


app = FastAPI(
    title="Forensic Sketch Generator API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    gen = get_generator()
    flux = get_flux_generator()
    torch = __import__("torch")
    return {
        "ok": True,
        "sd15_loaded": gen.is_loaded,
        "flux_loaded": flux.is_loaded,
        "sd15_model_id": settings.model_id,
        "flux_model_id": settings.flux_model_id,
        "flux_nf4_model_id": settings.flux_nf4_model_id,
        "flux_quant": settings.flux_quant,
        "flux_quantize_t5": settings.flux_quantize_t5,
        "flux_offload_mode": settings.flux_offload_mode,
        "cuda_available": torch.cuda.is_available(),
        "device": gen.device if gen.is_loaded else (
            "cuda" if torch.cuda.is_available() else "cpu"
        ),
    }


def _free_gpu_for(backend: str) -> None:
    """Only one heavy model may occupy the 4060 8GB at a time."""
    import torch

    sd = get_generator()
    flux = get_flux_generator()
    if backend == "flux" and sd.is_loaded:
        logger.info("Switching to Flux — unloading SD 1.5 first")
        sd.unload()
    if backend == "sd15" and flux.is_loaded:
        logger.info("Switching to SD 1.5 — unloading Flux first")
        flux.unload()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _generate_sd15(req: GenerateRequest, seed: int) -> GenerateResponse:
    _free_gpu_for("sd15")
    gen = get_generator()
    if not gen.is_loaded:
        gen.load()

    face_prompt = _with_sketch_style(req.prompt)
    sketch_prompt = face_prompt
    face_neg = req.negative_prompt or settings.face_negative_prompt
    sketch_neg = req.negative_prompt or settings.negative_prompt

    face, sketch = gen.generate_forensic_sketch(
        face_prompt=face_prompt,
        sketch_prompt=sketch_prompt,
        face_negative=face_neg,
        sketch_negative=sketch_neg,
        seed=seed,
        enable_refine=req.enable_refine,
    )

    out = sketch
    if req.enable_polish:
        out = apply_pencil_sketch(sketch)

    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in req.label)[:40]
    gen.save(out, prefix=f"api_sd15_{safe_label}_{seed}")

    return GenerateResponse(
        label=req.label,
        seed=seed,
        image_base64=_pil_to_b64(out),
        model="sd15",
    )


def _generate_flux(req: GenerateRequest, seed: int) -> GenerateResponse:
    # Critical on 8GB: unload SD before Flux device_map=cuda or the worker
    # hangs / ACCESS_VIOLATION → UI sees read ECONNRESET.
    _free_gpu_for("flux")
    flux = get_flux_generator()
    if not flux.is_loaded:
        logger.info("Lazy-loading FLUX.1-schnell NF4 (first request)…")
        flux.load()

    # Full prompt → pencil-sketch steered generation (style applied inside generator)
    face = flux.generate_forensic_face(prompt=req.prompt, seed=seed)

    # Always polish Flux to graphite look (OpenCV dodge/burn + edges)
    out = apply_pencil_sketch(face)

    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in req.label)[:40]
    flux.save(out, prefix=f"api_flux_sketch_{safe_label}_{seed}")

    return GenerateResponse(
        label=req.label,
        seed=seed,
        image_base64=_pil_to_b64(out),
        model="flux",
    )


def _generate_sync(req: GenerateRequest) -> GenerateResponse:
    seed = settings.seed if req.seed is None else int(req.seed)
    model = (req.model or "sd15").strip().lower()
    backend = backend_for_model(model)

    logger.info(
        "generate label=%s model=%s backend=%s seed=%s prompt_chars=%s",
        req.label,
        model,
        backend,
        seed,
        len(req.prompt),
    )

    if backend == "flux":
        return _generate_flux(req, seed)

    if backend == "sd15":
        return _generate_sd15(req, seed)

    raise HTTPException(
        status_code=400,
        detail=f"Model '{model}' is not available yet (backend={backend}). Use sd15 or flux.",
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    async with _gen_lock:
        try:
            return await asyncio.to_thread(_generate_sync, req)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Generation failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
