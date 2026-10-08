"""
Run ControlNet + LoRA compare via Colab (no frontend UI).

Requires:
  1) Colab notebook running (scripts/colab_server.py) with GPU + ngrok
  2) COLAB_API_URL set in repo-root .env

Preferred (direct to Colab — avoids local FastAPI double-timeout):
  .\\.venv\\Scripts\\python.exe scripts\\run_controlnet_to_outputs.py --direct-colab "30 year old male, oval face, short black hair, beard, front view"
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env (same pattern as api/main.py)
_env = ROOT / ".env"
if _env.is_file():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v

TIMEOUT_SEC = 900  # 15 min — two SD passes on Colab can be slow
HEADERS = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "1",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="ControlNet+LoRA → outputs/")
    parser.add_argument("description", nargs="?", default="")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cn-scale", type=float, default=0.75)
    parser.add_argument(
        "--backend",
        default=os.environ.get("PYTHON_BACKEND_URL", "http://127.0.0.1:8000"),
        help="Local FastAPI URL (only used without --direct-colab)",
    )
    parser.add_argument(
        "--direct-colab",
        action="store_true",
        default=True,
        help="Call COLAB_API_URL directly (default; recommended)",
    )
    parser.add_argument(
        "--via-local",
        action="store_true",
        help="Proxy through local FastAPI instead of calling Colab directly",
    )
    args = parser.parse_args()
    direct = not args.via_local

    description = args.description.strip()
    if not description:
        description = (
            "30-35 year old male, oval face, short black wavy hair, "
            "thick eyebrows, almond eyes, beard and mustache, front view, "
            "graphite pencil forensic sketch"
        )
        print("No description given — using default short prompt.")

    payload = {
        "description": description,
        "seed": args.seed,
        "controlnet_scale": args.cn_scale,
    }

    if direct:
        colab = os.environ.get("COLAB_API_URL", "").rstrip("/")
        if not colab:
            raise SystemExit("COLAB_API_URL missing in .env")
        health_url = f"{colab}/health"
        url = f"{colab}/compare"
    else:
        health_url = f"{args.backend.rstrip('/')}/health"
        url = f"{args.backend.rstrip('/')}/generate-controlnet-compare"

    print(f"Checking health: {health_url}")
    try:
        h = requests.get(health_url, headers=HEADERS, timeout=30)
        print(f"Health {h.status_code}: {h.text[:200]}")
        if h.status_code != 200:
            raise SystemExit(
                "Colab/backend health failed. Re-run Colab cell 5 and update COLAB_API_URL in .env."
            )
    except requests.RequestException as exc:
        raise SystemExit(
            f"Cannot reach worker ({exc}).\n"
            "1) Keep Colab GPU notebook running\n"
            "2) Re-run launch cell — copy NEW ngrok URL into .env COLAB_API_URL\n"
            "3) Retry with --direct-colab"
        ) from exc

    print(f"POST {url}  (timeout={TIMEOUT_SEC}s — can take 5–12 min)")
    print(f"seed={args.seed} cn_scale={args.cn_scale}")
    print(f"description: {description[:120]}...")

    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=TIMEOUT_SEC)
    except requests.exceptions.ReadTimeout as exc:
        raise SystemExit(
            f"Timed out after {TIMEOUT_SEC}s.\n"
            "Colab is still generating or hung. Check the Colab cell output.\n"
            "If ngrok URL changed, update .env and retry."
        ) from exc

    if resp.status_code != 200:
        raise SystemExit(f"Failed {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    saved = data.get("saved_paths") or {}
    if saved:
        print("Saved by FastAPI:")
        for k, p in saved.items():
            print(f"  {k}: {p}")
        return

    for key in ("baseline", "canny_edges", "controlnet_lora_refined"):
        b64 = data.get(key)
        if not b64:
            continue
        path = out_dir / f"controlnet_{key}_{stamp}_seed{args.seed}.png"
        path.write_bytes(base64.b64decode(b64))
        print(f"Saved {key}: {path}")


if __name__ == "__main__":
    main()
