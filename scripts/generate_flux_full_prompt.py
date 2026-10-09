"""
Warm-load NF4 FLUX and generate one full-prompt forensic face (outside the UI).

Run from repo root (with .venv activated):
  python scripts/generate_flux_full_prompt.py

Does NOT load SD 1.5 — frees RAM/VRAM for Flux on 8GB / 16GB machines.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("flux_full_prompt")

# Full prompt — intentionally longer than CLIP's 77 tokens (Experiment 1B)
FULL_PROMPT = (
    "Front-facing forensic facial composite portrait of an adult male, "
    "approximately mid-thirties, medium olive skin tone, oval face shape with "
    "slightly prominent cheekbones, dark brown almond-shaped eyes set average "
    "distance apart, moderately thick dark eyebrows with a gentle arch, "
    "straight medium-width nose with a rounded tip, full lips with a defined "
    "cupid's bow, short black hair parted on the left with a receding temples "
    "look, light stubble along the jawline, small mole on the left cheek below "
    "the eye, neutral closed-mouth expression, clear identity features, "
    "neutral studio lighting, plain light gray background, highly detailed "
    "facial anatomy suitable for witness identification"
)


def main() -> int:
    import torch

    from ai.flux_generator import get_flux_generator
    from utils.config import settings

    logger.info(
        "CUDA=%s | quant=%s | t5_4bit=%s | offload=%s | size=%sx%s | steps=%s",
        torch.cuda.is_available(),
        settings.flux_quant,
        settings.flux_quantize_t5,
        settings.flux_offload_mode,
        settings.flux_width,
        settings.flux_height,
        settings.flux_steps,
    )
    logger.info("Full prompt chars=%s (CLIP limit is ~77 tokens)", len(FULL_PROMPT))

    from ai.sketch_processor import apply_pencil_sketch

    flux = get_flux_generator()
    logger.info("Warm-loading FLUX (NF4)…")
    flux.load()
    logger.info("Generating full-prompt pencil sketch…")
    image = flux.generate_forensic_face(prompt=FULL_PROMPT, seed=settings.seed)
    sketch = apply_pencil_sketch(image)
    path = flux.save(sketch, prefix=f"flux_full_prompt_sketch_{settings.seed}")
    logger.info("Saved: %s", path)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
