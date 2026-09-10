"""
FastAPI image worker for Forensic Sketch Generator.

Wraps ai.image_generator (SD 1.5) so Next.js can request images over HTTP.
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

from ai.image_generator import get_generator
from ai.sketch_processor import apply_pencil_sketch
from utils.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forensic.api")

# Serialize GPU work — concurrent SD jobs on one GPU often OOM
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


class GenerateResponse(BaseModel):
    label: str
    seed: int
    image_base64: str
    mime_type: str = "image/png"


def _pil_to_b64(image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _with_sketch_style(prompt: str) -> str:
    p = prompt.strip()
    if "pencil" in p.lower() or "forensic" in p.lower():
        return p
    return p + SKETCH_SUFFIX


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading Stable Diffusion worker…")
    gen = get_generator()
    # Load in thread so startup does not block event loop forever without progress
    await asyncio.to_thread(gen.load)
    logger.info("SD worker ready on device=%s model=%s", gen.device, gen.model_id)
    yield


app = FastAPI(
    title="Forensic Sketch Generator API",
    version="0.1.0",
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
    return {
        "ok": True,
        "model_loaded": gen.is_loaded,
        "model_id": settings.model_id,
        "device": gen.device if gen.is_loaded else ("cuda" if __import__("torch").cuda.is_available() else "cpu"),
    }


def _generate_sync(req: GenerateRequest) -> GenerateResponse:
    gen = get_generator()
    if not gen.is_loaded:
        gen.load()

    seed = settings.seed if req.seed is None else int(req.seed)
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

    # Persist for debugging / phase-04 artifacts
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in req.label)[:40]
    gen.save(out, prefix=f"api_{safe_label}_{seed}")

    return GenerateResponse(
        label=req.label,
        seed=seed,
        image_base64=_pil_to_b64(out),
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    async with _gen_lock:
        try:
            return await asyncio.to_thread(_generate_sync, req)
        except Exception as exc:
            logger.exception("Generation failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
