# Legacy Streamlit UI (retired)

Product UI is now **Next.js** (`forenisic/`) + **FastAPI** (`api/main.py`).

This folder keeps the old Streamlit demo for reference only:

- `app_streamlit.py` — former root `app.py`
- `ui/` — Streamlit helpers
- `.streamlit/` — theme config

To run the old UI (requires `pip install streamlit` separately):

```bash
# from Forensic-Sketch-Generator/ (repo product root)
pip install streamlit
streamlit run legacy/app_streamlit.py
```

You may need to adjust `sys.path` / imports if modules moved.

**Do not use Streamlit for day-to-day demos** — use the two-process flow in the main README.
