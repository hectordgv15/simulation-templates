# import streamlit as st
# import streamlit.components.v1 as components
# import yaml
# from pathlib import Path

# from prompts.prompts_engine import PromptOrchestrator


# # ----------------------------
# # Utils
# # ----------------------------
# @st.cache_data(show_spinner=False)
# def load_yaml(path: Path):
#     return yaml.safe_load(path.read_text(encoding="utf-8"))

# def md_to_html(markdown_text: str) -> str:
#     try:
#         import markdown as md
#         body = md.markdown(
#             markdown_text,
#             extensions=["extra", "tables", "fenced_code", "sane_lists"],
#         )
#     except Exception:
#         body = f"<pre>{markdown_text}</pre>"

#     # HTML minimal (sin “card” fancy)
#     return f"""
#     <!doctype html>
#     <html lang="es">
#     <head>
#       <meta charset="utf-8"/>
#       <meta name="viewport" content="width=device-width, initial-scale=1"/>
#       <style>
#         body {{
#           margin: 18px;
#           font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
#           line-height: 1.55;
#           color: #111;
#         }}
#         pre {{
#           padding: 12px;
#           border: 1px solid #e6e6e6;
#           border-radius: 10px;
#           overflow-x: auto;
#           background: #fafafa;
#         }}
#         code {{
#           background: #f4f4f4;
#           padding: 0.15rem 0.35rem;
#           border-radius: 6px;
#         }}
#         table {{
#           border-collapse: collapse;
#           width: 100%;
#           margin: 12px 0;
#         }}
#         th, td {{
#           border: 1px solid #e6e6e6;
#           padding: 8px 10px;
#           vertical-align: top;
#         }}
#         th {{ background: #fafafa; text-align: left; }}
#         blockquote {{
#           margin: 12px 0;
#           padding: 8px 12px;
#           border-left: 3px solid #ddd;
#           background: #fafafa;
#         }}
#       </style>
#     </head>
#     <body>
#       {body}
#     </body>
#     </html>
#     """


# # ----------------------------
# # Minimal UI config
# # ----------------------------
# st.set_page_config(page_title="Prompt Viewer", layout="wide")

# st.markdown(
#     """
#     <style>
#       .block-container { max-width: 1200px; padding-top: 1.2rem; }
#       section[data-testid="stSidebar"] { border-right: 1px solid #eee; }
#       .stButton button, .stDownloadButton button { border-radius: 10px; }
#       /* Reduce un poco el “ruido” */
#       header[data-testid="stHeader"] { height: 0.5rem; }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# st.title("🧩 Prompt Viewer")
# st.caption("Visualiza tus prompts (Markdown/HTML) y ajusta solo los parámetros permitidos.")


# # ----------------------------
# # Paths
# # ----------------------------
# ROOT = Path(__file__).resolve().parent
# base_fields = ROOT / "prompts" / "fields"
# base_premises = ROOT / "prompts" / "premises"

# table_field_path = base_fields / "019_maturities.yaml"
# macro_field_path = base_fields / "063_cfo_ir.yaml"
# evaluation_info_path = base_premises / "question_17.yaml"

# missing = [p for p in [table_field_path, macro_field_path, evaluation_info_path] if not p.exists()]
# if missing:
#     st.error("No encuentro estos archivos:\n\n" + "\n".join([f"- {m}" for m in missing]))
#     st.stop()

# table_field = load_yaml(table_field_path)
# macro_field = load_yaml(macro_field_path)
# evaluation_info = load_yaml(evaluation_info_path)


# # ----------------------------
# # Sidebar controls (compact)
# # ----------------------------
# with st.sidebar:
#     st.subheader("Parámetros")

#     output_language = st.selectbox(
#         "output_language",
#         options=["es", "en"],
#         index=0,
#     )

#     st.divider()
#     st.caption("max_words")

#     def none_or_int(label, default):
#         options = ["None", "50", "100", "150", "200", "300", "500", "800", "1200"]
#         idx = options.index(str(default)) if default is not None else 0
#         val = st.selectbox(label, options, index=idx)
#         return None if val == "None" else int(val)

#     mw_extract_quant = none_or_int("Extract Quantitative", None)
#     mw_crit_quant    = none_or_int("Critique Quantitative", 150)
#     mw_extract_qual  = none_or_int("Extract Qualitative", 500)
#     mw_crit_qual     = none_or_int("Critique Qualitative", 150)
#     mw_summary       = none_or_int("Summarize", 150)

#     st.divider()
#     st.caption("Flags")

#     include_specifications = st.checkbox("include_specifications", value=True)
#     include_exclusions     = st.checkbox("include_exclusions", value=True)
#     include_source_guides  = st.checkbox("include_source_guides", value=True)


# # ----------------------------
# # Build prompts (solo con params permitidos)
# # ----------------------------
# extract_quantitative = PromptOrchestrator.get_prompt(
#     "extract",
#     **table_field,
#     field_type="quantitative",
#     output_language=output_language,
#     max_words=mw_extract_quant,
#     include_specifications=include_specifications,
#     include_exclusions=include_exclusions,
#     include_source_guides=include_source_guides,
# )

# critique_quantitative = PromptOrchestrator.get_prompt(
#     "critique",
#     **table_field,
#     field_type="quantitative",
#     output_language=output_language,
#     max_words=mw_crit_quant,
# )

# extract_qualitative = PromptOrchestrator.get_prompt(
#     "extract",
#     **macro_field,
#     field_type="qualitative",
#     output_language=output_language,
#     max_words=mw_extract_qual,
#     include_source_guides=include_source_guides,
# )

# critique_qualitative = PromptOrchestrator.get_prompt(
#     "critique",
#     **macro_field,
#     field_type="qualitative",
#     output_language=output_language,
#     max_words=mw_crit_qual,
# )

# evaluation_prompt = PromptOrchestrator.get_prompt(
#     "evaluate",
#     **evaluation_info,
#     output_language    = output_language,
#     premise_id         = "strategic_planning",
#     objective_premise  = evaluation_info["premises"]["strategic_planning"]["description"],
    
# )

# summary_prompt = PromptOrchestrator.get_prompt(
#     "summarize",
#     include_judgment=True,
#     max_words=mw_summary,
# )

# prompts = {
#     "Extract • Quantitative": extract_quantitative,
#     "Critique • Quantitative": critique_quantitative,
#     "Extract • Qualitative": extract_qualitative,
#     "Critique • Qualitative": critique_qualitative,
#     "Evaluate": evaluation_prompt,
#     "Summarize": summary_prompt,
# }

# # ----------------------------
# # Main: selector + viewer
# # ----------------------------
# col1, col2, col3 = st.columns([2.2, 1, 1])

# with col1:
#     selected = st.selectbox("Prompt", list(prompts.keys()))
# content = prompts[selected]
# html = md_to_html(content)


# st.divider()

# tab_md, tab_html, tab_raw = st.tabs(["Markdown", "HTML preview", "Raw"])

# with tab_md:
#     st.markdown(content)

# with tab_html:
#     # Preview limpio, sin scroll excesivo
#     components.html(html, height=700, scrolling=True)

# with tab_raw:
#     st.code(content, language="markdown")




import streamlit as st
import streamlit.components.v1 as components
import yaml
from pathlib import Path

from prompts.prompts_engine import PromptOrchestrator


# ----------------------------
# Utils
# ----------------------------
@st.cache_data(show_spinner=False)
def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def md_to_html(markdown_text: str) -> str:
    try:
        import markdown as md
        body = md.markdown(
            markdown_text,
            extensions=["extra", "tables", "fenced_code", "sane_lists"],
        )
    except Exception:
        body = f"<pre>{markdown_text}</pre>"

    return f"""
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <style>
        :root {{
          --text: #0f172a;
          --muted: #475569;
          --border: #e2e8f0;
          --bg: #ffffff;
          --card: #ffffff;
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
        h1, h2, h3 {{
          letter-spacing: -0.02em;
          margin: 0.8rem 0 0.4rem;
        }}
        p, li {{
          color: var(--text);
        }}
        a {{
          color: var(--accent);
          text-decoration: none;
        }}
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
        pre code {{
          background: transparent;
          padding: 0;
          color: inherit;
        }}

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
        th {{
          background: var(--soft);
          text-align: left;
          color: #0b1220;
        }}
        tr:nth-child(even) td {{
          background: #fbfdff;
        }}

        blockquote {{
          margin: 14px 0;
          padding: 10px 12px;
          border-left: 4px solid var(--border);
          background: var(--soft);
          border-radius: 12px;
          color: var(--muted);
        }}
        hr {{
          border: none;
          border-top: 1px solid var(--border);
          margin: 16px 0;
        }}
      </style>
    </head>
    <body>
      {body}
    </body>
    </html>
    """


# ----------------------------
# App config
# ----------------------------
st.set_page_config(page_title="Prompt Viewer", layout="wide")

st.markdown(
    """
    <style>
      :root{
        --border: #e6edf5;
        --muted: #64748b;
        --text: #0f172a;
        --soft: #f8fafc;
      }

      /* Layout */
      .block-container { max-width: 1250px; padding-top: 1.25rem; padding-bottom: 2.25rem; }
      header[data-testid="stHeader"] { height: 0.35rem; }
      section[data-testid="stSidebar"] { border-right: 1px solid var(--border); background: #fbfcfe; }
      [data-testid="stSidebar"] .block-container { padding-top: 1.1rem; }

      /* Widgets */
      .stButton button, .stDownloadButton button {
        border-radius: 12px !important;
        padding: 0.55rem 0.85rem !important;
      }
      .stDownloadButton button { border: 1px solid var(--border); }
      .stSelectbox div[data-baseweb="select"] > div { border-radius: 12px; }
      .stCheckbox { padding: 0.2rem 0; }

      /* Tabs a lo “pro” */
      .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid var(--border);
      }
      .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 10px 12px;
      }
      .stTabs [aria-selected="true"] {
        background: white;
        border: 1px solid var(--border);
        border-bottom: 0;
      }

      /* Cards / hero */
      .hero {
        border: 1px solid var(--border);
        background: linear-gradient(135deg, #f7f7ff 0%, #ffffff 40%, #f3fbff 100%);
        border-radius: 18px;
        padding: 18px 18px 14px 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
      }
      .hero-title {
        font-size: 1.55rem;
        font-weight: 750;
        color: var(--text);
        letter-spacing: -0.02em;
        margin-bottom: 4px;
      }
      .hero-subtitle {
        color: var(--muted);
        font-size: 0.98rem;
        margin-bottom: 10px;
      }
      .chip {
        display: inline-block;
        border: 1px solid var(--border);
        background: #ffffff;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.85rem;
        color: var(--muted);
        margin-right: 6px;
        margin-bottom: 6px;
      }
      .card {
        border: 1px solid var(--border);
        background: white;
        border-radius: 16px;
        padding: 14px 14px 10px 14px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.03);
      }
      .card-title {
        font-weight: 700;
        color: var(--text);
        margin-bottom: 6px;
      }
      .card-note {
        color: var(--muted);
        font-size: 0.92rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------
# Paths
# ----------------------------
ROOT = Path(__file__).resolve().parent
base_fields = ROOT / "prompts" / "fields"
base_premises = ROOT / "prompts" / "premises"

table_field_path = base_fields / "019_maturities.yaml"
macro_field_path = base_fields / "063_cfo_ir.yaml"
evaluation_info_path = base_premises / "question_17.yaml"

missing = [p for p in [table_field_path, macro_field_path, evaluation_info_path] if not p.exists()]
if missing:
    st.error("No encuentro estos archivos:\n\n" + "\n".join([f"- {m}" for m in missing]))
    st.stop()

table_field = load_yaml(table_field_path)
macro_field = load_yaml(macro_field_path)
evaluation_info = load_yaml(evaluation_info_path)


# ----------------------------
# Template registry
# ----------------------------
PROMPT_OPTIONS = [
    "Extract • Quantitative",
    "Critique • Quantitative",
    "Extract • Qualitative",
    "Critique • Qualitative",
    "Evaluate",
    "Summarize",
]

DEFAULT_MAX_WORDS = {
    "Extract • Quantitative": None,
    "Critique • Quantitative": 150,
    "Extract • Qualitative": 500,
    "Critique • Qualitative": 150,
    "Evaluate": None,
    "Summarize": 150,
}

MAX_WORDS_OPTIONS = [None, 50, 100, 150, 200, 300, 500, 800, 1200]


# ----------------------------
# Session state init / sync
# ----------------------------
if "selected_prompt" not in st.session_state:
    st.session_state["selected_prompt"] = PROMPT_OPTIONS[0]

if "max_words" not in st.session_state:
    st.session_state["max_words"] = DEFAULT_MAX_WORDS.get(st.session_state["selected_prompt"], None)

def sync_max_words_default():
    sel = st.session_state["selected_prompt"]
    st.session_state["max_words"] = DEFAULT_MAX_WORDS.get(sel, None)


# ----------------------------
# Sidebar (más limpio y contextual)
# ----------------------------
with st.sidebar:
    st.subheader("Configuración")

    st.selectbox(
        "Plantilla",
        PROMPT_OPTIONS,
        key="selected_prompt",
        on_change=sync_max_words_default,
        help="Selecciona la plantilla/prompt. El max_words se aplica solo al prompt seleccionado.",
    )

    output_language = st.selectbox(
        "Idioma de salida",
        options=["es", "en"],
        index=0,
    )

    st.divider()

    st.caption("Límite de longitud (aplica al prompt seleccionado)")
    st.selectbox(
        "max_words",
        options=MAX_WORDS_OPTIONS,
        key="max_words",
        index=MAX_WORDS_OPTIONS.index(st.session_state["max_words"]) if st.session_state["max_words"] in MAX_WORDS_OPTIONS else 0,
        format_func=lambda x: "Sin límite" if x is None else str(x),
    )

    st.divider()

    # Opciones avanzadas SOLO cuando tienen sentido
    selected = st.session_state["selected_prompt"]
    with st.expander("Opciones avanzadas", expanded=False):
        # Defaults (para evitar NameError fuera del expander)
        include_specifications = True
        include_exclusions = True
        include_source_guides = True

        if selected in ("Extract • Quantitative", "Extract • Qualitative"):
            st.caption("Flags (solo Extract)")
            include_specifications = st.checkbox("include_specifications", value=True)
            include_exclusions = st.checkbox("include_exclusions", value=True)
            include_source_guides = st.checkbox("include_source_guides", value=True)
        elif selected == "Summarize":
            st.caption("No hay flags adicionales para Summarize en esta vista.")
        else:
            st.caption("Esta plantilla no expone flags configurables aquí.")

    # Guardamos flags “fuera” del expander con valores por defecto si no tocaba mostrarlos
    if selected not in ("Extract • Quantitative", "Extract • Qualitative"):
        include_specifications = True
        include_exclusions = True
        include_source_guides = True


# ----------------------------
# Build only the selected prompt
# ----------------------------
def build_prompt(selected_name: str, max_words, output_language: str):
    if selected_name == "Extract • Quantitative":
        return PromptOrchestrator.get_prompt(
            "extract",
            **table_field,
            field_type="quantitative",
            output_language=output_language,
            max_words=max_words,
            include_specifications=include_specifications,
            include_exclusions=include_exclusions,
            include_source_guides=include_source_guides,
        )

    if selected_name == "Critique • Quantitative":
        return PromptOrchestrator.get_prompt(
            "critique",
            **table_field,
            field_type="quantitative",
            output_language=output_language,
            max_words=max_words,
        )

    if selected_name == "Extract • Qualitative":
        return PromptOrchestrator.get_prompt(
            "extract",
            **macro_field,
            field_type="qualitative",
            output_language=output_language,
            max_words=max_words,
            include_source_guides=include_source_guides,
        )

    if selected_name == "Critique • Qualitative":
        return PromptOrchestrator.get_prompt(
            "critique",
            **macro_field,
            field_type="qualitative",
            output_language=output_language,
            max_words=max_words,
        )

    if selected_name == "Evaluate":
        return PromptOrchestrator.get_prompt(
            "evaluate",
            **evaluation_info,
            output_language=output_language,
            premise_id="strategic_planning",
            objective_premise=evaluation_info["premises"]["strategic_planning"]["description"],
        )

    if selected_name == "Summarize":
        return PromptOrchestrator.get_prompt(
            "summarize",
            include_judgment=True,
            max_words=max_words,
        )

    raise ValueError(f"Plantilla no soportada: {selected_name}")


selected = st.session_state["selected_prompt"]
max_words = st.session_state["max_words"]
content = build_prompt(selected, max_words, output_language)
html = md_to_html(content)


# ----------------------------
# Front (más “pro”)
# ----------------------------
mw_label = "Sin límite" if max_words is None else str(max_words)
word_count = len(content.split())

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-title">Prompt Viewer</div>
      <div class="hero-subtitle">Visualiza y exporta prompts (Markdown/HTML) ajustando solo parámetros permitidos.</div>
      <span class="chip">Plantilla: <b>{selected}</b></span>
      <span class="chip">Idioma: <b>{output_language.upper()}</b></span>
      <span class="chip">max_words: <b>{mw_label}</b></span>
      <span class="chip">Palabras (actual): <b>{word_count}</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([3, 1])

with top_left:
    st.markdown(
        """
        <div class="card">
          <div class="card-title">Vista previa</div>
          <div class="card-note">Cambia plantilla y parámetros en el panel lateral. El contenido se regenera al vuelo.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    st.markdown(
        """
        <div class="card">
          <div class="card-title">Acciones</div>
          <div class="card-note">Exporta el prompt actual para usarlo fuera.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        "⬇️ Descargar .md",
        data=content,
        file_name=f"{selected.replace('•','-').replace(' ','_').lower()}.md",
        mime="text/markdown",
        use_container_width=True,
    )

st.divider()

tab_md, tab_html, tab_raw = st.tabs(["Markdown", "HTML preview", "Raw"])

with tab_md:
    st.markdown(content)

with tab_html:
    components.html(html, height=720, scrolling=True)

with tab_raw:
    st.code(content, language="markdown")
