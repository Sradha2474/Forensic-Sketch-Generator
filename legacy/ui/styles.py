"""Modern ChatGPT / Perplexity / Cursor inspired Streamlit theme."""

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --bg0: #05070d;
  --bg1: #0a0e18;
  --glass: rgba(18, 22, 36, 0.78);
  --glass-strong: rgba(24, 28, 46, 0.92);
  --glass-border: rgba(148, 163, 255, 0.22);
  --text: #eef2ff;
  --mute: #a0a9c8;
  --blue: #5b8cff;
  --purple: #a78bfa;
  --grad: linear-gradient(135deg, #4f7cff 0%, #8b5cf6 55%, #c084fc 100%);
  --grad-soft: linear-gradient(135deg, rgba(79,124,255,0.18), rgba(139,92,246,0.14));
  --ok: #34d399;
  --radius: 22px;
}

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--text);
}

.stApp {
  background:
    radial-gradient(1000px 520px at 8% -12%, rgba(79,124,255,0.28), transparent 58%),
    radial-gradient(900px 480px at 100% -5%, rgba(167,139,250,0.24), transparent 52%),
    radial-gradient(700px 420px at 70% 100%, rgba(79,124,255,0.10), transparent 55%),
    linear-gradient(180deg, var(--bg0), var(--bg1) 40%, #080b14);
  color: var(--text);
}

.block-container {
  padding-top: 1.2rem !important;
  padding-bottom: 2.5rem !important;
  max-width: 1280px !important;
}

#MainMenu, footer, header { visibility: hidden; }

/* Navbar */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 1.2rem;
  margin-bottom: 1.25rem;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(22,26,42,0.92), rgba(14,17,28,0.88));
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(22px);
  box-shadow:
    0 18px 50px rgba(0,0,0,0.35),
    inset 0 1px 0 rgba(255,255,255,0.05);
  animation: fadeUp 0.45s ease both;
}
.nav-left {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.nav-logo {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--grad);
  box-shadow: 0 8px 24px rgba(79,124,255,0.4);
  font-size: 1.1rem;
}
.nav-brand {
  font-family: 'Space Grotesk', Inter, sans-serif;
  font-weight: 700;
  font-size: 1.08rem;
  letter-spacing: -0.02em;
}
.nav-brand span {
  display: block;
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--mute);
  letter-spacing: 0.02em;
  margin-top: 0.1rem;
  font-family: Inter, sans-serif;
}
.nav-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.38rem 0.85rem;
  border-radius: 999px;
  color: #e8ecff;
  background: var(--grad-soft);
  border: 1px solid rgba(167,139,250,0.4);
  box-shadow: 0 0 24px rgba(139,92,246,0.15);
}

/* Glass cards */
.glass-card {
  position: relative;
  background: var(--glass);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius);
  padding: 1.45rem 1.4rem 1.25rem;
  backdrop-filter: blur(22px);
  box-shadow:
    0 22px 60px rgba(0,0,0,0.38),
    inset 0 1px 0 rgba(255,255,255,0.05);
  margin-bottom: 0.9rem;
  overflow: hidden;
  animation: fadeUp 0.55s ease both;
}
.glass-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 2px;
  background: var(--grad);
  opacity: 0.85;
}
.panel-kicker {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #c4b5fd;
  margin-bottom: 0.55rem;
}
.panel-title {
  font-family: 'Space Grotesk', Inter, sans-serif;
  font-size: 1.72rem;
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.15;
  margin: 0 0 0.55rem 0;
  background: var(--grad);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.panel-sub {
  color: var(--mute);
  font-size: 0.96rem;
  line-height: 1.6;
  margin: 0 0 1.15rem 0;
  max-width: 38rem;
}
.section-label {
  color: #c7d0ef;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin: 0.55rem 0 0.6rem;
}
.step-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0 0 1rem 0;
}
.step-chip {
  font-size: 0.74rem;
  font-weight: 600;
  color: #dbe3ff;
  padding: 0.32rem 0.7rem;
  border-radius: 999px;
  background: rgba(79,124,255,0.12);
  border: 1px solid rgba(139,156,255,0.22);
}
.step-chip b {
  color: #a78bfa;
  margin-right: 0.25rem;
}

/* Placeholder */
.empty-stage {
  min-height: 460px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 0.75rem;
  border-radius: 18px;
  border: 1px dashed rgba(167,139,250,0.35);
  background:
    radial-gradient(circle at 50% 30%, rgba(79,124,255,0.16), transparent 52%),
    radial-gradient(circle at 80% 80%, rgba(139,92,246,0.10), transparent 45%),
    rgba(8, 10, 18, 0.55);
  color: var(--mute);
  padding: 2.2rem 1.4rem;
  position: relative;
  overflow: hidden;
}
.empty-stage::after {
  content: "";
  position: absolute;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: rgba(79,124,255,0.12);
  filter: blur(40px);
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  animation: pulse 3.2s ease-in-out infinite;
}
.empty-stage .glyph {
  position: relative;
  z-index: 1;
  width: 84px;
  height: 84px;
  border-radius: 24px;
  display: grid;
  place-items: center;
  font-size: 2.15rem;
  background: var(--grad);
  color: white;
  box-shadow: 0 16px 40px rgba(79,124,255,0.45);
  animation: floaty 3.5s ease-in-out infinite;
}
.empty-stage h3 {
  position: relative;
  z-index: 1;
  margin: 0;
  color: var(--text);
  font-family: 'Space Grotesk', Inter, sans-serif;
  font-size: 1.3rem;
}
.empty-stage p {
  position: relative;
  z-index: 1;
  max-width: 26rem;
  line-height: 1.55;
  margin: 0;
}
.image-frame {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(167,139,250,0.28);
  box-shadow: 0 16px 40px rgba(0,0,0,0.35);
  background: #0a0c14;
}
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  background: rgba(52,211,153,0.12);
  color: var(--ok);
  border: 1px solid rgba(52,211,153,0.32);
  box-shadow: 0 0 20px rgba(52,211,153,0.08);
}
.status-pill .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 10px var(--ok);
}
.prompt-box {
  background: linear-gradient(180deg, rgba(10,12,22,0.9), rgba(8,10,18,0.75));
  border: 1px solid rgba(139,156,255,0.18);
  border-radius: 14px;
  padding: 0.95rem 1rem;
  color: #d2daf5;
  font-size: 0.88rem;
  line-height: 1.55;
  white-space: pre-wrap;
}
.tip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.85rem 0 0.2rem;
}
.tip {
  font-size: 0.74rem;
  color: #b8c2e6;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-7px); }
}
@keyframes pulse {
  0%, 100% { opacity: 0.45; transform: translateX(-50%) scale(1); }
  50% { opacity: 0.8; transform: translateX(-50%) scale(1.08); }
}

/* Streamlit widget polish */
div[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a0d16, #07090f);
  border-right: 1px solid var(--glass-border);
}
div[data-testid="stTextArea"] textarea {
  background: rgba(7,9,16,0.82) !important;
  border: 1px solid rgba(139,156,255,0.24) !important;
  border-radius: 16px !important;
  color: var(--text) !important;
  min-height: 180px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
div[data-testid="stTextArea"] textarea:focus {
  border-color: rgba(167,139,250,0.55) !important;
  box-shadow: 0 0 0 3px rgba(79,124,255,0.18) !important;
}
div.stButton > button {
  border-radius: 999px !important;
  border: 1px solid rgba(139,156,255,0.28) !important;
  background: rgba(18, 22, 36, 0.95) !important;
  color: var(--text) !important;
  font-weight: 650 !important;
  padding: 0.62rem 1.05rem !important;
  transition: 0.18s ease;
}
div.stButton > button:hover {
  border-color: rgba(167,139,250,0.65) !important;
  box-shadow: 0 0 0 4px rgba(79,124,255,0.14);
  transform: translateY(-1px);
}
div.stButton > button[kind="primary"] {
  background: var(--grad) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 12px 32px rgba(79,124,255,0.4);
  font-size: 1rem !important;
  padding: 0.78rem 1.1rem !important;
}
div.stButton > button[kind="primary"]:hover {
  filter: brightness(1.06);
  box-shadow: 0 14px 36px rgba(139,92,246,0.45);
}
div[data-testid="stStatus"] {
  background: rgba(16,20,32,0.88);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
}
div[data-testid="stImage"] img {
  border-radius: 14px;
}
</style>
"""


def inject_theme() -> None:
    import streamlit as st

    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_navbar(badge: str = "MVP Demo") -> None:
    import streamlit as st

    st.markdown(
        f"""
<div class="top-nav">
  <div class="nav-left">
    <div class="nav-logo">🕵️</div>
    <div class="nav-brand">
      AI Forensic Sketch Generator
      <span>Witness description → graphite composite</span>
    </div>
  </div>
  <div class="nav-badge">{badge}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def empty_preview() -> None:
    import streamlit as st

    st.markdown(
        """
<div class="empty-stage">
  <div class="glyph">✏️</div>
  <h3>No sketch generated yet.</h3>
  <p>Describe the suspect on the left. Use AI Suggest to refine the wording,
  then generate a forensic pencil sketch.</p>
</div>
""",
        unsafe_allow_html=True,
    )
