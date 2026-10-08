"""
Photo → Canny → ControlNet + LoRA sketch (structure from REAL photo).

1) On Colab: interrupt old server, paste scripts/colab_paste_photo_endpoint.py, run it
2) Put new ngrok URL in .env as COLAB_API_URL
3) Run:
   .\\.venv\\Scripts\\python.exe scripts\\run_controlnet_from_photo.py outputs\\ref_passport_woman.jpg
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

_env = ROOT / ".env"
if _env.is_file():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k:
            os.environ[k] = v  # always refresh from .env

HEADERS = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "1"}
TIMEOUT = 900

DEFAULT_DESC = (
    "young South Asian woman early 20s, friendly gentle face, oval face, "
    "soft full cheeks, rounded chin, thick WAVY dark hair past shoulders, "
    "dark almond eyes, subtle closed-lip smile, natural dark eyebrows, "
    "tiny nose stud on left nostril, white collared button-down shirt, "
    "thin chain necklace, front-facing forensic pencil sketch"
)


def _prepare_image_b64(path: Path) -> str:
    """Resize to 512 and JPEG-compress so ngrok/Colab don't choke on huge payloads."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    img = img.resize((512, 512), resample)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "image",
        nargs="?",
        default=str(ROOT / "outputs" / "ref_passport_woman.jpg"),
    )
    parser.add_argument("--description", default=DEFAULT_DESC)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cn-scale", type=float, default=0.95)
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.is_file():
        raise SystemExit(f"Image not found: {img_path}")

    colab = os.environ.get("COLAB_API_URL", "").rstrip("/")
    if not colab:
        raise SystemExit("COLAB_API_URL missing in .env")

    print("Health…", colab)
    h = requests.get(f"{colab}/health", headers=HEADERS, timeout=30)
    print(h.status_code, h.text[:300])
    if h.status_code != 200:
        raise SystemExit("Colab health failed")

    if "photo-v2" not in h.text:
        print(
            "\n*** Colab is not running the FIX cell (photo-v2). ***\n"
            "1) Interrupt Colab uvicorn cell\n"
            "2) Paste & run scripts/colab_paste_photo_endpoint.py\n"
            "3) Copy NEW ngrok URL into .env\n"
            "4) Re-run this script\n"
        )

    b64 = _prepare_image_b64(img_path)
    print(f"Payload image ~{len(b64) // 1024} KB base64")

    payload = {
        "image_base64": b64,
        "description": args.description,
        "seed": args.seed,
        "controlnet_scale": args.cn_scale,
    }
    url = f"{colab}/sketch-from-photo"
    print(f"POST {url} cn_scale={args.cn_scale}")
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=TIMEOUT)

    if resp.status_code == 404:
        raise SystemExit("404 — /sketch-from-photo missing. Paste the FIX cell on Colab.")

    # Endpoint may return 200 with {"ok": false, "error": ...}
    try:
        data = resp.json()
    except Exception:
        raise SystemExit(f"Failed {resp.status_code}: {resp.text[:800]}")

    if resp.status_code != 200 or data.get("ok") is False or data.get("error"):
        print("COLAB ERROR:", data.get("error") or resp.text[:800])
        if data.get("trace"):
            print(data["trace"][:2000])
        raise SystemExit(
            "Colab generation failed — see error above (also check Colab cell log)."
        )

    if "controlnet_lora_refined" not in data:
        raise SystemExit(f"Unexpected response keys: {list(data.keys())}")

    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for key in ("photo_resized", "canny_edges", "controlnet_lora_refined"):
        raw = data.get(key)
        if not raw:
            continue
        path = out_dir / f"photo_cn_{key}_{stamp}_seed{args.seed}.png"
        path.write_bytes(base64.b64decode(raw))
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
