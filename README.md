# AI-Assisted Forensic Sketch Generator

Next.js interview UI + FastAPI Stable Diffusion worker. Produces **draft vs LLM-refined** forensic sketches for research comparison.

| Layer | Stack |
|---|---|
| UI / interview / LLM refine | Next.js (`forenisic/`) · OpenRouter |
| Image worker | FastAPI · Diffusers **SD 1.5** · OpenCV polish |
| Legacy | Streamlit demo archived under `legacy/` |

---

## Architecture

```text
Next.js forensic.tsx
    │  interview (40 Q) → structured profile → model picker
    │  → prompt_router (micro | original) → OpenRouter refine
    ▼
POST /api/generate-compare
    │
    ├─► POST :8000/generate  (draft prompt, seed 42, model=sd15)
    └─► POST :8000/generate  (LLM prompt,  seed 42, model=sd15)
            │
            ▼
        SD 1.5 txt2img → img2img → polish
            │
            ▼
        Side-by-side: Draft Prompt → Face | LLM Prompt → Face
```

Same seed + same negatives so the only intentional variable is the positive prompt. Jobs run sequentially through the bridge (CPU-friendly timeouts).

---

## Experiment 1A (CelebA baseline)

Dataset-driven baseline (**no random UI answers**). Maps a real CelebA face (`Expermiment/001089.jpg`) into the interview schema, runs Draft vs LLM → SD 1.5 (seed 42), and records CLIP truncation + attribute accuracy.

See [`experiments/README.md`](experiments/README.md).

```bash
# worker must be running on :8000
python experiments/scripts/run_experiment_1a_celeba.py --image-id 001089.jpg --case-id celeba_001
```

Artifacts: `experiments/dataset_baseline/celeba_001/`

---

## Experiment 1B (Micro prompt + model router)

Keep the **original** full prompt builder. Add a **micro** (≤77-token) builder and a **router**:

```text
forenisic/lib/prompts/
  original_prompt.ts   ← wraps existing prompt-builder.ts (unchanged)
  micro_prompt.ts      ← NEW ≤77-token prompt
  prompt_router.ts     ← model → micro | original
```

| Model | Prompt | Status |
|-------|--------|--------|
| SD 1.5 | micro | live |
| SD 1.5 + ControlNet | micro | coming soon |
| SDXL | micro | coming soon |
| Flux | original (full) | coming soon |
| SD 3 | original (full) | coming soon |

UI flow: finish 40 questions → **choose model** → router builds draft → LLM refine (mode-aware) → generate.

---

## Quick start (two processes)

### 1. Python worker (Terminal A)

`api/` lives in the **nested product folder**, not the outer research journal root.

```bash
# If you are in D:\Forensic-Sketch-Generator (outer journal):
cd Forensic-Sketch-Generator

python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Or from the outer journal root: double-click / run `run-backend.bat` (cds into the product folder for you).

Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

First run downloads SD 1.5 into `model_cache/`.

### 2. Next.js UI (Terminal B)

```bash
cd forenisic
cp .env.example .env   # if needed
# edit .env — see env vars below
npm install
npm run dev
```

Or `run-forensic-ui.bat`.

Open [http://localhost:3000](http://localhost:3000) → finish the interview → see **Draft Prompt → Generated Face | LLM Prompt → Generated Face** (same seed).

---

## Environment variables (`forenisic/.env`)

```env
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4o-mini
PYTHON_BACKEND_URL=http://127.0.0.1:8000
```

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | Server-side LLM refine (`/api/refine-prompt`) |
| `OPENROUTER_MODEL` | Optional; default `openai/gpt-4o-mini` |
| `PYTHON_BACKEND_URL` | FastAPI base URL for `/api/generate-compare` |

Restart `npm run dev` after changing `.env`.

---

## API surface

### FastAPI (`:8000`)

| Method | Path | Body / notes |
|---|---|---|
| `GET` | `/health` | Model loaded / device |
| `POST` | `/generate` | `{ prompt, negative_prompt?, seed?, label? }` → `{ label, seed, image_base64 }` |

### Next.js

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/refine-prompt` | OpenRouter rewrite |
| `POST` | `/api/generate-compare` | `{ draft, final }` → both images via `Promise.all` |

---

## Project structure

```text
Forensic-Sketch-Generator/
├── api/main.py              # FastAPI SD worker
├── ai/                      # ImageGenerator, prompts, polish (keep)
├── utils/config.py
├── forenisic/               # Next.js product UI
│   ├── app/api/generate-compare/
│   ├── components/forensic.tsx
│   └── .env
├── legacy/                  # Retired Streamlit UI
├── outputs/                 # Saved PNGs
├── model_cache/
├── requirements.txt
├── run-backend.bat
└── run-forensic-ui.bat
```

---

## Tests

```bash
pytest tests/ -q
```

---

## Ethics

Education and research only. Do not treat generated sketches as courtroom evidence.

---

## Authors

STAAR · C.V. Raman Global University  
**Sradha Ram** · Tusharkanta Behera · Sandeep Kumar Swain  
Supervisor: **Dr. Sukant Kishoro Bisoy**
