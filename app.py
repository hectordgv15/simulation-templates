# app_prompt_viewer.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import streamlit as st
import streamlit.components.v1 as components

# Import your real loader (adjust the path if your module name differs)
# from prompts.loader import load_prompts, BASE_FIELDS, BASE_QUESTIONS
from prompts.prompts_loader import load_prompts, BASE_FIELDS, BASE_QUESTIONS


# ----------------------------
# Utils
# ----------------------------
def md_to_html(markdown_text: str) -> str:
    """Render Markdown -> HTML (fallback to <pre> if markdown lib fails)."""
    try:
        import markdown as md  # pip install markdown

        body = md.markdown(
            markdown_text,
            extensions=["extra", "tables", "fenced_code", "sane_lists"],
        )
    except Exception:
        body = f"<pre>{markdown_text}</pre>"

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <style>
        :root {{
          --text: #0f172a;
          --muted: #475569;
          --border: #e2e8f0;
          --bg: #ffffff;
          --codebg: #0b1020;
          --codefg: #e5e7eb;
          --soft: #f8fafc;
          --accent: #2563eb;
        }}
        body {{
          margin: 18px;
          font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
          line-height: 1.6;
          color: var(--text);
          background: var(--bg);
        }}
        h1, h2, h3 {{ letter-spacing: -0.02em; margin: 0.8rem 0 0.4rem; }}
        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        pre {{
          padding: 14px;
          border: 1px solid var(--border);
          border-radius: 14px;
          overflow-x: auto;
          background: var(--codebg);
          color: var(--codefg);
        }}
        code {{
          background: rgba(2, 6, 23, 0.06);
          padding: 0.15rem 0.35rem;
          border-radius: 8px;
          font-size: 0.95em;
        }}
        pre code {{ background: transparent; padding: 0; color: inherit; }}

        table {{
          border-collapse: collapse;
          width: 100%;
          margin: 14px 0;
          border: 1px solid var(--border);
          border-radius: 14px;
          overflow: hidden;
        }}
        th, td {{
          border-bottom: 1px solid var(--border);
          padding: 10px 12px;
          vertical-align: top;
        }}
        th {{ background: var(--soft); text-align: left; color: #0b1220; }}
        tr:nth-child(even) td {{ background: #fbfdff; }}

        blockquote {{
          margin: 14px 0;
          padding: 10px 12px;
          border-left: 4px solid var(--border);
          background: var(--soft);
          border-radius: 12px;
          color: var(--muted);
        }}
        hr {{ border: none; border-top: 1px solid var(--border); margin: 16px 0; }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """


def safe_filename(s: str) -> str:
    s = s.strip().lower()
    for ch in [" ", "/", "\\", ":", "|", "•", "."]:
        s = s.replace(ch, "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s


def short_label(s: str, max_len: int = 26) -> str:
    return s if len(s) <= max_len else (s[: max_len - 1] + "…")


def list_yaml_stems(folder: Path) -> list[str]:
    if not folder.exists():
        return []
    return sorted([p.stem for p in folder.glob("*.yaml")])


def flatten_prompts(data: Any, prefix: str = "") -> Iterable[Tuple[str, str]]:
    """Convert loader output (dict/str/other) into a list of (key_path, markdown_str)."""
    if isinstance(data, str):
        yield (prefix or "prompt", data)
        return

    if isinstance(data, dict):
        for k, v in data.items():
            new_prefix = f"{prefix}.{k}" if prefix else str(k)
            yield from flatten_prompts(v, new_prefix)
        return

    yield (prefix or "value", str(data))


@st.cache_data(show_spinner=False)
def cached_load_prompts(process: str, name: str) -> Dict[str, Any]:
    if process == "extraction":
        return load_prompts(process=process, field_name=name)
    return load_prompts(process=process, question_name=name)


# ----------------------------
# App
# ----------------------------
st.set_page_config(page_title="Prompt Viewer", layout="wide")

st.markdown(
    """
    <style>
      :root{
        --border: #dbe7ff;
        --muted: #5b6b85;
        --text: #0f172a;

        /* Lighter sidebar blues */
        --sb-bg-top: #f3f8ff;
        --sb-bg-mid: #f8fbff;
        --sb-bg-bottom: #ffffff;
        --sb-border: #d6e6ff;
        --sb-accent: #60a5fa;
        --sb-text: #0b2a6b;

        /* Lighter button theme */
        --btn-bg: #60a5fa;
        --btn-bg-hover: #3b82f6;
        --btn-bg-active: #2563eb;
        --btn-fg: #ffffff;
        --btn-border: rgba(96,165,250,0.40);
        --btn-shadow: 0 10px 20px rgba(96,165,250,0.18);
      }

      .block-container { max-width: 1400px; padding-top: 1.1rem; padding-bottom: 2rem; }
      header[data-testid="stHeader"] { height: 0.35rem; }

      /* Sidebar background */
      section[data-testid="stSidebar"] {
        border-right: 1px solid var(--sb-border);
        background:
          radial-gradient(1200px 400px at 20% 0%, rgba(96,165,250,0.16) 0%, rgba(96,165,250,0) 55%),
          linear-gradient(180deg, var(--sb-bg-top) 0%, var(--sb-bg-mid) 55%, var(--sb-bg-bottom) 100%);
      }
      [data-testid="stSidebar"] .block-container { padding-top: 1.1rem; }

      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] .stCaption {
        color: var(--sb-text) !important;
      }

      /* Make sidebar widget "cards" same width (fixes Field being wider than Process/View) */
      [data-testid="stSidebar"] .stRadio,
      [data-testid="stSidebar"] .stSelectbox {
        width: 100% !important;
        display: block !important;
        box-sizing: border-box !important;

        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(214,230,255,0.95);
        border-radius: 18px;
        padding: 12px 12px 10px 12px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
      }

      /* Keep widget labels consistent */
      [data-testid="stSidebar"] label[data-testid="stWidgetLabel"]{
        margin-bottom: 6px !important;
      }

      /* Sidebar radio options: uniform "button" backgrounds and consistent size */
      [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        width: 100% !important;
        min-height: 42px !important;
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;

        padding: 10px 12px !important;
        margin: 6px 0 !important;

        background: rgba(255,255,255,0.78) !important;
        border: 1px solid rgba(214,230,255,0.95) !important;
        border-radius: 14px !important;
      }
      [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.92) !important;
      }
      [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:focus-within {
        outline: 2px solid rgba(96,165,250,0.28) !important;
        outline-offset: 2px !important;
      }

      /* Selectbox internal control: align height/radius with radio options */
      [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
        min-height: 42px !important;
        border-radius: 14px !important;
        border-color: rgba(214,230,255,0.95) !important;
      }

      /* Prompt + download buttons: add background and unify height */
      .stButton button, .stDownloadButton button {
        border-radius: 14px !important;
        padding: 0.55rem 0.85rem !important;

        background: var(--btn-bg) !important;
        color: var(--btn-fg) !important;
        border: 1px solid var(--btn-border) !important;
        box-shadow: var(--btn-shadow) !important;

        min-height: 42px !important;
      }
      .stButton button:hover, .stDownloadButton button:hover {
        background: var(--btn-bg-hover) !important;
      }
      .stButton button:active, .stDownloadButton button:active {
        background: var(--btn-bg-active) !important;
        transform: translateY(1px);
      }
      /* Prevent text wrapping inside buttons (keeps consistent height) */
      .stButton button > div, .stDownloadButton button > div {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
      }

      .hero {
        border: 1px solid #e6edf5;
        background: linear-gradient(135deg, #f7f7ff 0%, #ffffff 40%, #f3fbff 100%);
        border-radius: 18px;
        padding: 18px 18px 14px 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
      }
      .hero-title { font-size: 1.55rem; font-weight: 780; letter-spacing: -0.02em; margin-bottom: 4px; color: var(--text); }
      .hero-subtitle { color: var(--muted); font-size: 0.98rem; margin-bottom: 0; }

      .panel {
        border: 1px solid #e6edf5;
        background: white;
        border-radius: 18px;
        padding: 14px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.03);
        margin-bottom: 12px;
      }
      .panel-title { font-weight: 850; margin-bottom: 8px; color: var(--text); }
      .meta { color: #64748b; font-size: 0.92rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Prompt Viewer</div>
      <p class="hero-subtitle">
        Select a <b>field</b> (extraction) or a <b>question</b> (evaluation), then switch prompts using the horizontal buttons.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Settings")

    process_label = st.radio("Process", ["Extraction", "Evaluation"], index=0)
    process = "extraction" if process_label == "Extraction" else "evaluation"

    base_dir = BASE_FIELDS if process == "extraction" else BASE_QUESTIONS
    items = list_yaml_stems(base_dir)

    if not items:
        st.warning(f"No YAML files found in: {base_dir}")
        selected = None
    else:
        label = "Field" if process == "extraction" else "Question"
        selected = st.selectbox(label, items, index=0)

    view_mode = st.radio("View", ["HTML", "Markdown"], index=0)

if not selected:
    st.stop()

# Load prompts
try:
    prompts_obj = cached_load_prompts(process, selected)
except Exception as e:
    st.error(f"Error generating prompts: {e}")
    st.stop()

flat = list(flatten_prompts(prompts_obj))
keys = [k for k, _ in flat]
by_key = {k: v for k, v in flat}

if not keys:
    st.info("No prompts were generated.")
    st.stop()

# Selected prompt state
state_key = "selected_prompt_key"
if state_key not in st.session_state or st.session_state[state_key] not in by_key:
    st.session_state[state_key] = keys[0]

# ----------------------------
# Horizontal prompt bar (grid)
# ----------------------------
st.markdown(
    f"""
    <div class="panel">
      <div class="panel-title">Prompts</div>
      <div class="meta">{len(keys)} prompts for <b>{process}</b> / <b>{selected}</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# How many buttons per row (higher = more compact)
PER_ROW = 5

for i in range(0, len(keys), PER_ROW):
    row = keys[i : i + PER_ROW]
    cols = st.columns(len(row), gap="small")
    for c, k in zip(cols, row):
        is_active = k == st.session_state[state_key]
        btn_text = f"✅ {short_label(k)}" if is_active else short_label(k)
        with c:
            if st.button(
                btn_text,
                use_container_width=True,
                key=f"btn__{safe_filename(process + '__' + selected + '__' + k)}",
            ):
                st.session_state[state_key] = k
                st.rerun()

# ----------------------------
# Viewer
# ----------------------------
st.markdown(
    f"""
    <div class="panel">
      <div class="panel-title">Preview</div>
      <div class="meta"><b>Selected:</b> <code>{st.session_state[state_key]}</code></div>
    </div>
    """,
    unsafe_allow_html=True,
)

sel = st.session_state[state_key]
md_text = by_key.get(sel, "")
file_stub = safe_filename(f"{process}__{selected}__{sel}")

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    st.download_button(
        label="⬇️ Download .md",
        data=md_text,
        file_name=f"{file_stub}.md",
        mime="text/markdown",
        use_container_width=True,
        key=f"dl_md__{file_stub}",
    )
with c2:
    st.download_button(
        label="⬇️ Download .txt",
        data=md_text,
        file_name=f"{file_stub}.txt",
        mime="text/plain",
        use_container_width=True,
        key=f"dl_txt__{file_stub}",
    )
with c3:
    st.caption(f"Source: `{process} / {selected}`")

st.markdown("")

if view_mode == "HTML":
    components.html(md_to_html(md_text), height=640, scrolling=True)
else:
    st.code(md_text, language="markdown")
