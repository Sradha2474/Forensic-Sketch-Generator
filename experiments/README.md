# Experiment 1A — CelebA Dataset-Driven Baseline

**Purpose:** Document the current SD 1.5 pipeline using a *real* CelebA face and ground-truth attributes — **not** random Next.js interview answers.

Research finding this supports:

> Our initial SD 1.5 implementation was evaluated using the complete generated prompts. The prompts exceeded the CLIP context limit, resulting in truncation. Faces were generated under CLIP’s 77-token truncation constraint.

This experiment does **not** compress prompts (that is Experiment 1B).

## Assets

Source files live in [`Expermiment/`](../Expermiment/) (typo folder name preserved):

| File | Role |
|------|------|
| `001089.jpg` | Reference face (`celeba_001`) |
| `list_attr_celeba.txt` | CelebA binary attributes |
| `list_landmarks_align_celeba.txt` | 5-point landmarks |

## Pipeline

```text
CelebA image + attributes + landmarks
        ↓
ground_truth.json
        ↓
converter (mapped attrs only; else not_available)
        ↓
interview_90.json
        ↓
existing TS normalizer + prompt builder → draft_prompt.txt
        ↓
OpenRouter refine → llm_prompt.txt
        ↓
SD 1.5 seed=42 (txt2img → img2img → OpenCV) × 2
        ↓
generated_draft.png / generated_llm.png
        ↓
CLIP zero-shot attribute accuracy vs CelebA GT
```

**Converter rule:** if CelebA has no evidence for an interview field, the value is `not_available`. Never invent `"medium"`.

## Output folder

```text
experiments/dataset_baseline/celeba_001/
  reference.jpg
  celeba_attributes.txt
  ground_truth.json
  interview_90.json
  draft_prompt.txt
  llm_prompt.txt
  generated_draft.png
  generated_llm.png
  evaluation.json
  manifest.json
```

`manifest.json` records CLIP token metrics (`token_count_full`, `clip_max_length: 77`, `truncated`) and the full pipeline stages (txt2img / img2img / OpenCV).  
`token_count_effective` is a baseline vs the 77 limit — not a claim of Diffusers’ exact internal token sequence.

## How to run

```bash
# Terminal A — SD worker
cd Forensic-Sketch-Generator
.\.venv\Scripts\Activate.ps1   # or source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal B — experiment
python experiments/scripts/run_experiment_1a_celeba.py --image-id 001089.jpg --case-id celeba_001
```

Optional flags:

- `--skip-generate` — build GT / interview / prompts only (no GPU)
- `--skip-eval` — skip CLIP attribute scoring
- `--backend http://127.0.0.1:8000`
- `--seed 42`

Requires:

- `Expermiment/` assets present
- Node/`npx tsx` available (draft prompt uses the same TS modules as the UI)
- `OPENROUTER_API_KEY` in `forenisic/.env` for the LLM arm (if missing, LLM arm falls back to the draft prompt and records the error)

## Evaluation

`evaluation.json` includes:

- Draft / LLM CLIP truncation metrics
- Attribute table over CelebA labels that have probes
- `attribute_accuracy_draft` / `attribute_accuracy_llm` = correct / evaluated attributes

Only **available CelebA attributes** are scored — not invented geometry.

## Scripts

| Script | Role |
|--------|------|
| `scripts/celeba_loader.py` | Load attrs + landmarks |
| `scripts/celeba_to_interview90.py` | CelebA → interview schema |
| `scripts/build_prompts_from_interview90.ts` | Draft prompt via existing UI libs |
| `scripts/clip_attr_eval.py` | CLIP zero-shot attribute probes |
| `scripts/run_experiment_1a_celeba.py` | End-to-end Experiment 1A runner |
