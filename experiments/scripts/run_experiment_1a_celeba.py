#!/usr/bin/env python3
"""
Experiment 1A — CelebA dataset-driven baseline (no Next.js random interview).

Flow:
  CelebA image + attrs → interview_90.json → draft/LLM prompts → SD 1.5 (seed 42)
  → save artifacts + CLIP token metrics + attribute accuracy

Example:
  python experiments/scripts/run_experiment_1a_celeba.py --image-id 001089.jpg --case-id celeba_001
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow importing sibling modules
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from celeba_loader import (  # noqa: E402
    DEFAULT_EXPERIMENT_ASSETS,
    build_ground_truth,
    load_celeba_attributes,
    load_celeba_landmarks,
    load_raw_attr_line,
)
from celeba_to_interview90 import (  # noqa: E402
    celeba_to_interview90,
    mapped_keys_summary,
)
from clip_attr_eval import evaluate_image_against_gt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CLIP_MAX_LENGTH = 77
DEFAULT_SEED = 42
DEFAULT_BACKEND = os.environ.get("PYTHON_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def count_clip_tokens(prompt: str) -> dict[str, Any]:
    """
    Count tokens with CLIPTokenizer (same family as SD 1.5 text encoder).
    token_count_effective is a baseline vs clip_max_length=77, not a claim of
    Diffusers' exact internal sequence (special-token / truncation internals).
    """
    from transformers import CLIPTokenizer

    tok = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
    ids = tok(prompt, truncation=False, add_special_tokens=True).input_ids
    full = len(ids)
    truncated = full > CLIP_MAX_LENGTH
    return {
        "token_count_full": full,
        "clip_max_length": CLIP_MAX_LENGTH,
        "truncated": truncated,
        "token_count_effective": min(full, CLIP_MAX_LENGTH),
    }


def build_draft_via_tsx(interview_path: Path, out_json: Path) -> dict[str, Any]:
    ts = SCRIPTS / "build_prompts_from_interview90.ts"
    # Windows: npx.cmd; prefer shell so PATH resolves npm shims
    cmd = f'npx --yes tsx "{ts}" "{interview_path}" "{out_json}"'
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT / "forenisic"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"tsx prompt build failed ({proc.returncode}):\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return json.loads(out_json.read_text(encoding="utf-8"))


def refine_prompt_openrouter(
    structured_values: Any,
    draft_positive: str,
    draft_negative: str,
) -> dict[str, Any]:
    """Call OpenRouter directly (same role as /api/refine-prompt)."""
    api_key = (
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("openrouter_api_key")
    )
    if not api_key:
        return {
            "ok": False,
            "error": "Missing OPENROUTER_API_KEY",
            "prompt": None,
            "model": None,
        }

    model = os.environ.get("OPENROUTER_MODEL") or "openai/gpt-4o-mini"
    system = (
        "You are a forensic prompt engineer for face-image generation (SD 1.5).\n"
        "Rewrite structured face attributes into ONE clear natural English description.\n"
        "Keep ALL factual attributes; do not invent missing ones.\n"
        "Return ONLY JSON: {\"positive\": \"...\", \"negative\": \"...\"}"
    )
    user = "\n".join(
        [
            "STRUCTURED FACE ATTRIBUTES (canonical):",
            json.dumps(structured_values, indent=2),
            "",
            "DRAFT POSITIVE PROMPT:",
            draft_positive,
            "",
            "DRAFT NEGATIVE PROMPT:",
            draft_negative,
            "",
            "Rewrite into the required JSON.",
        ]
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Forensic Experiment 1A",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "prompt": None, "model": model}

    content = data["choices"][0]["message"]["content"]
    # Strip markdown fences if present
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": f"LLM returned non-JSON: {content[:200]}",
            "prompt": None,
            "model": model,
        }
    return {
        "ok": True,
        "prompt": {
            "positive": parsed.get("positive", ""),
            "negative": parsed.get("negative", draft_negative),
        },
        "model": model,
        "error": None,
    }


def call_generate(
    backend: str,
    prompt: str,
    negative_prompt: str | None,
    seed: int,
    label: str,
) -> dict[str, Any]:
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "label": label,
        "enable_refine": True,
        "enable_polish": True,
    }
    req = urllib.request.Request(
        f"{backend}/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=1800) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"FastAPI /generate failed ({backend}): {exc}. "
            "Start: uvicorn api.main:app --host 0.0.0.0 --port 8000"
        ) from exc


def save_b64_png(b64: str, path: Path) -> None:
    path.write_bytes(base64.b64decode(b64))


def pipeline_block() -> dict[str, Any]:
    return {
        "model": "runwayml/stable-diffusion-v1-5",
        "same_prompt_for_txt2img_and_img2img": True,
        "txt2img": {"steps": 28, "guidance_scale": 7.5},
        "img2img": {"strength": 0.58, "steps": 28, "guidance_scale": 8.0},
        "opencv": "apply_pencil_sketch",
    }


def run_case(
    image_id: str,
    case_id: str,
    seed: int,
    backend: str,
    skip_generate: bool,
    skip_eval: bool,
) -> Path:
    _load_dotenv(ROOT / "forenisic" / ".env")
    _load_dotenv(ROOT / ".env")

    assets = DEFAULT_EXPERIMENT_ASSETS
    src_img = assets / image_id
    if not src_img.is_file():
        raise FileNotFoundError(f"Reference image not found: {src_img}")

    out_dir = ROOT / "experiments" / "dataset_baseline" / case_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- ground truth ---
    attrs = load_celeba_attributes(image_id)
    landmarks = load_celeba_landmarks(image_id)
    gt = build_ground_truth(image_id, attrs=attrs, landmarks=landmarks)
    (out_dir / "ground_truth.json").write_text(
        json.dumps(gt, indent=2), encoding="utf-8"
    )

    header, data_line = load_raw_attr_line(image_id)
    (out_dir / "celeba_attributes.txt").write_text(
        header + "\n" + data_line + "\n", encoding="utf-8"
    )

    shutil.copy2(src_img, out_dir / "reference.jpg")

    # --- interview_90 ---
    interview = celeba_to_interview90(image_id, attrs=attrs)
    (out_dir / "interview_90.json").write_text(
        json.dumps(interview, indent=2), encoding="utf-8"
    )
    summary = mapped_keys_summary(interview)
    print("[1A] interview:", summary)

    # --- draft prompt (existing TS builder) ---
    draft_json_path = out_dir / "_draft_build.json"
    draft_payload = build_draft_via_tsx(out_dir / "interview_90.json", draft_json_path)
    draft_pos = draft_payload["draft_positive"]
    draft_neg = draft_payload["draft_negative"]
    (out_dir / "draft_prompt.txt").write_text(draft_pos, encoding="utf-8")
    print(f"[1A] draft prompt chars={len(draft_pos)}")

    # --- LLM prompt ---
    llm_result = refine_prompt_openrouter(
        draft_payload.get("structured_values"),
        draft_pos,
        draft_neg,
    )
    if llm_result["ok"]:
        llm_pos = llm_result["prompt"]["positive"]
        llm_neg = llm_result["prompt"]["negative"]
        llm_model = llm_result["model"]
        llm_error = None
    else:
        llm_pos = draft_pos
        llm_neg = draft_neg
        llm_model = None
        llm_error = llm_result.get("error")
        print(f"[1A] LLM refine skipped/failed: {llm_error} — using draft for LLM arm")
    (out_dir / "llm_prompt.txt").write_text(llm_pos, encoding="utf-8")

    draft_tokens = count_clip_tokens(draft_pos)
    llm_tokens = count_clip_tokens(llm_pos)
    print("[1A] draft tokens:", draft_tokens)
    print("[1A] llm tokens:", llm_tokens)

    draft_img = out_dir / "generated_draft.png"
    llm_img = out_dir / "generated_llm.png"

    gen_draft_meta: dict[str, Any] = {}
    gen_llm_meta: dict[str, Any] = {}

    if not skip_generate:
        print(f"[1A] generating draft face via {backend} seed={seed} …")
        gen_d = call_generate(backend, draft_pos, draft_neg, seed, "draft")
        save_b64_png(gen_d["image_base64"], draft_img)
        gen_draft_meta = {"seed": gen_d.get("seed", seed), "label": gen_d.get("label")}

        print(f"[1A] generating LLM face via {backend} seed={seed} …")
        gen_l = call_generate(backend, llm_pos, llm_neg, seed, "llm")
        save_b64_png(gen_l["image_base64"], llm_img)
        gen_llm_meta = {"seed": gen_l.get("seed", seed), "label": gen_l.get("label")}
    else:
        print("[1A] --skip-generate: leaving placeholder images if missing")
        if not draft_img.is_file():
            shutil.copy2(src_img, draft_img)
        if not llm_img.is_file():
            shutil.copy2(src_img, llm_img)

    # --- evaluation ---
    evaluation: dict[str, Any] = {
        "experiment": "1A",
        "case_id": case_id,
        "image_id": image_id,
        "seed": seed,
        "clip_truncation": {
            "draft": draft_tokens,
            "llm": llm_tokens,
        },
        "llm_refine": {
            "ok": bool(llm_result["ok"]),
            "model": llm_model,
            "error": llm_error,
        },
        "notes": (
            "Faces generated under CLIP's 77-token truncation constraint when "
            "token_count_full > clip_max_length. token_count_effective is a baseline "
            "measurement against the 77 limit, not Diffusers' exact internal sequence."
        ),
    }

    if not skip_eval and draft_img.is_file() and llm_img.is_file():
        print("[1A] CLIP attribute evaluation …")
        # Focus eval table on attributes that matter for this case (present in GT file)
        # Use full available_attributes as plan specifies
        draft_eval = evaluate_image_against_gt(draft_img, attrs)
        llm_eval = evaluate_image_against_gt(llm_img, attrs)
        evaluation["draft"] = draft_eval
        evaluation["llm"] = llm_eval
        evaluation["attribute_accuracy_draft"] = draft_eval["attribute_accuracy"]
        evaluation["attribute_accuracy_llm"] = llm_eval["attribute_accuracy"]
        # Side-by-side table
        table = []
        by_attr_d = {r["attribute"]: r for r in draft_eval["rows"]}
        by_attr_l = {r["attribute"]: r for r in llm_eval["rows"]}
        for attr in sorted(set(by_attr_d) | set(by_attr_l)):
            table.append(
                {
                    "attribute": attr,
                    "ground_truth": by_attr_d.get(attr, by_attr_l.get(attr, {})).get(
                        "ground_truth"
                    ),
                    "generated_draft": by_attr_d.get(attr, {}).get("predicted"),
                    "generated_llm": by_attr_l.get(attr, {}).get("predicted"),
                    "draft_correct": by_attr_d.get(attr, {}).get("correct"),
                    "llm_correct": by_attr_l.get(attr, {}).get("correct"),
                }
            )
        evaluation["attribute_table"] = table
    else:
        evaluation["skipped_eval"] = skip_eval

    (out_dir / "evaluation.json").write_text(
        json.dumps(evaluation, indent=2), encoding="utf-8"
    )

    manifest = {
        "experiment": "1A",
        "hypothesis": (
            "Baseline: full prompts exceed CLIP 77 and faces are generated under "
            "CLIP's 77-token truncation constraint"
        ),
        "notes": (
            "token_count_effective is a baseline measurement against clip_max_length=77, "
            "not a claim of the exact Diffusers/CLIP internal sequence. "
            "Worker logs truncation warnings when limits are exceeded."
        ),
        "run_id": f"{case_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "case_id": case_id,
        "image_id": image_id,
        "seed": seed,
        "clip_max_length": CLIP_MAX_LENGTH,
        "interview_summary": summary,
        "pipeline": pipeline_block(),
        "prompt_draft": {
            "file": "draft_prompt.txt",
            **draft_tokens,
            "seed": seed,
            "image": "generated_draft.png",
            "generation": gen_draft_meta,
        },
        "prompt_llm": {
            "file": "llm_prompt.txt",
            **llm_tokens,
            "seed": seed,
            "image": "generated_llm.png",
            "generation": gen_llm_meta,
            "refined_by": llm_model,
            "refine_error": llm_error,
        },
        "artifacts": [
            "reference.jpg",
            "celeba_attributes.txt",
            "ground_truth.json",
            "interview_90.json",
            "draft_prompt.txt",
            "llm_prompt.txt",
            "generated_draft.png",
            "generated_llm.png",
            "evaluation.json",
            "manifest.json",
        ],
        "backend": backend,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # cleanup temp
    if draft_json_path.is_file():
        draft_json_path.unlink()

    print(f"[1A] DONE → {out_dir}")
    return out_dir


def main() -> None:
    p = argparse.ArgumentParser(description="Experiment 1A CelebA baseline")
    p.add_argument("--image-id", default="001089.jpg")
    p.add_argument("--case-id", default="celeba_001")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--backend", default=DEFAULT_BACKEND)
    p.add_argument(
        "--skip-generate",
        action="store_true",
        help="Build GT/interview/prompts only; skip SD (or reuse images)",
    )
    p.add_argument(
        "--skip-eval",
        action="store_true",
        help="Skip CLIP attribute evaluation",
    )
    args = p.parse_args()
    run_case(
        image_id=args.image_id,
        case_id=args.case_id,
        seed=args.seed,
        backend=args.backend.rstrip("/"),
        skip_generate=args.skip_generate,
        skip_eval=args.skip_eval,
    )


if __name__ == "__main__":
    main()
