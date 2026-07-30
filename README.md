# 🕵️ AI-Assisted Forensic Sketch Generator

### Transform witness descriptions into graphite forensic composites — in seconds.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.60-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Diffusers](https://img.shields.io/badge/🤗%20Diffusers-SD%201.5-FFD21E?style=for-the-badge)](https://huggingface.co/docs/diffusers)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<p align="center">
  <img src="https://img.shields.io/badge/STAAR%20MVP-50%25%20Research%20Demo-8B5CF6?style=flat-square" />
  <img src="https://img.shields.io/badge/UI-Dark%20Glassmorphism-4F7CFF?style=flat-square" />
  <img src="https://img.shields.io/badge/Pipeline-txt2img%20→%20img2img%20→%20polish-34D399?style=flat-square" />
</p>

---

## ✨ What is this?

Law enforcement composites usually need a skilled forensic artist. This **MVP** lets an investigator (or witness) **type a description**, optionally **improve it with AI**, then generate a **forensic pencil-style sketch** using Stable Diffusion.

> Built as a realistic **50% STAAR research demo** — polished enough to present, modular enough to grow into the full system (interview agent, LoRA sketch model, database search).

---

## 🖥️ Product UI

| Left panel | Right panel |
|---|---|
| Witness description box | Empty sketchboard → final sketch |
| 🎤 Voice (placeholder) | Prompt used |
| ✨ AI Suggest Description | Status + download |
| 🎨 Generate Sketch | Generate again |

**Theme:** dark mode · glass cards · blue/purple accents · ChatGPT / Cursor inspired.

---

## 🧠 How it works

```text
Witness text
    │
    ▼
✨ AI description enhancer   (structured forensic wording)
    │
    ▼
Prompt engineer              (CLIP-safe forensic sketch prompt)
    │
    ├─► SD txt2img           clear face
    │
    └─► SD img2img           graphite pencil refine
            │
            ▼
        Dodge & burn polish  (report Phase-4 style transfer)
            │
            ▼
        Streamlit sketchboard + download
```

**Important:** raw witness text is never sent straight to the model. The system always builds an improved description and a clean forensic prompt first.

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (custom CSS glass UI) |
| Description AI | Rule-based enhancer (LLM-ready stub) |
| Generation | Hugging Face **Diffusers** · **Stable Diffusion v1.5** |
| Runtime | **PyTorch** (CPU or CUDA) |
| Sketch polish | OpenCV dodge & burn + Laplacian edges |
| Packaging | Modular `ai/` · `ui/` · `utils/` · `extensions/` |

---

## 🚀 Quick start

```bash
git clone https://github.com/Sradha2474/Forensic-Sketch-Generator.git
cd Forensic-Sketch-Generator

python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

> First run downloads SD 1.5 weights into `model_cache/` (one-time). CPU works; GPU is much faster.

---

## 🎮 Demo flow

1. Type something short: `Man with beard.`
2. Click **✨ AI Suggest Description**
3. Review / edit the improved text
4. Click **🎨 Generate Sketch**
5. Download the PNG

Example engineered prompt style:

> *A realistic forensic facial sketch of a male, approximately 35 years old, oval face, medium complexion, full black beard… pencil sketch, front view, highly detailed forensic style.*

---

## 📁 Project structure

```text
Forensic-Sketch-Generator/
├── app.py                      # Streamlit product UI
├── requirements.txt
├── README.md
├── .streamlit/config.toml      # Dark theme
├── ai/
│   ├── description_enhancer.py # Improve witness notes
│   ├── forensic_prompt.py      # Clean SD prompts
│   ├── prompt_builder.py       # Structured profile → prompt
│   ├── image_generator.py      # txt2img + img2img
│   └── sketch_processor.py     # Dodge & burn polish
├── ui/
│   └── styles.py               # Glassmorphism theme
├── utils/
│   ├── config.py
│   └── profile.py              # JSON witness profile schema
├── extensions/                 # Future: agent, edit, eval, DB
├── tests/
└── outputs/                    # Saved sketches (gitignored)
```

---

## 🔮 Roadmap (beyond this MVP)

| Module | Status | Path |
|---|---|---|
| Conversational interview agent | Stub | `extensions/interview_agent.py` |
| Sketch LoRA fine-tune | Planned | replace img2img refine |
| Selective region editing | Stub | `extensions/selective_edit.py` |
| Evaluation metrics | Stub | `extensions/evaluation.py` |
| Criminal gallery search | Stub | `extensions/database_search.py` |

---

## 🧪 Tests

```bash
pytest tests/ -q
```

---

## ⚠️ Ethics

For **education and research** only. Do not treat generated sketches as courtroom evidence. Models can inherit dataset bias — involve trained professionals for real investigations.

---

## 👩‍💻 Authors

STAAR project · C.V. Raman Global University  
**Sradha Ram** · Tusharkanta Behera · Sandeep Kumar Swain  
Supervisor: **Dr. Sukant Kishoro Bisoy**

Repo: [Sradha2474/Forensic-Sketch-Generator](https://github.com/Sradha2474/Forensic-Sketch-Generator)

---

<p align="center">
  <b>Bridge witness memory and visual evidence with AI.</b><br/>
  ★ Star the repo if this helps your research.
</p>
