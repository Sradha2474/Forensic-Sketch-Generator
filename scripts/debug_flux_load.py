"""NF4 Flux: device_map=cuda (package-recommended)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import torch

from ai.flux_generator import _hf_token
from utils.config import settings

LOG = ROOT / "outputs" / "flux_load_debug.txt"


def mark(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    mark(f"cuda={torch.cuda.is_available()} torch={torch.__version__}")
    if torch.cuda.is_available():
        free, total = torch.cuda.mem_get_info()
        mark(f"vram free={free/1e9:.2f}GiB total={total/1e9:.2f}GiB")

    token = _hf_token()
    nf4 = settings.flux_nf4_model_id

    from diffusers import FluxPipeline

    mark("C loading with device_map=cuda ...")
    pipe = FluxPipeline.from_pretrained(
        nf4,
        torch_dtype=torch.float16,
        cache_dir=settings.cache_dir,
        token=token,
        device_map="cuda",
    )
    mark("C pipeline ready")
    try:
        pipe.vae.enable_slicing()
        pipe.vae.enable_tiling()
    except Exception:
        pass

    if torch.cuda.is_available():
        free, total = torch.cuda.mem_get_info()
        mark(f"vram after load free={free/1e9:.2f}GiB")

    mark("C generating full prompt 512...")
    img = pipe(
        prompt=(
            "Front-facing forensic facial composite portrait of an adult male, "
            "mid-thirties, medium olive skin, oval face, dark brown almond eyes, "
            "thick dark eyebrows, straight medium nose, full lips, short black hair, "
            "light stubble, small mole on left cheek, neutral expression, studio lighting, "
            "plain background, highly detailed facial anatomy for witness identification"
        ),
        guidance_scale=0.0,
        num_inference_steps=4,
        max_sequence_length=256,
        width=512,
        height=512,
        generator=torch.Generator("cpu").manual_seed(42),
    ).images[0]
    out = ROOT / "outputs" / "flux_full_prompt_42.png"
    img.save(out)
    mark(f"C SAVED {out}")
    mark("ALL STEPS OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        mark(f"EXCEPTION: {type(exc).__name__}: {exc}")
        raise
