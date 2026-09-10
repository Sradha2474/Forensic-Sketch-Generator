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
    │  interview → normalize → structured → draft prompt
    │  → OpenRouter refine → final prompt
    ▼
POST /api/generate-compare   (Promise.all)
    │
    ├─► POST :8000/generate  (draft prompt, seed 42)
    └─► POST :8000/generate  (final prompt, seed 43)
            │
            ▼
        SD txt2img → img2img pencil → dodge/burn polish
            │
            ▼
        Side-by-side images in the UI
```

GPU jobs are serialized inside FastAPI (lock) so one card does not OOM; Next still fires both requests concurrently.

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

Open [http://localhost:3000](http://localhost:3000) → finish the interview → see **Draft | LLM-refined** sketches.

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
