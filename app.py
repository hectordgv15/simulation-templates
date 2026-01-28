import streamlit as st
import streamlit.components.v1 as components
import yaml
from pathlib import Path

from prompts.prompts_engine import PromptOrchestrator


# Utilities
# ---------------------------------------------------------------------------------------------------------------
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
        h1, h2, h3 {{
          letter-spacing: -0.02em;
          margin: 0.8rem 0 0.4rem;
        }}
        p, li {{ color: var(--text); }}
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
        tr:nth-child(even) td {{ background: #fbfdff; }}

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


def sanitize_key(s: str) -> str:
    return (
        s.lower()
        .replace("•", "-")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("__", "_")
    )


def scope_key(template_name: str, field_type: str | None) -> str:
    if template_name in ("Extract", "Critique"):
        return f"{template_name}__{field_type}"
    return template_name


def key_for(scope: str, param_name: str) -> str:
    return f"p__{sanitize_key(scope)}__{param_name}"


def ensure_state(scope: str, param_name: str, default):
    k = key_for(scope, param_name)
    if k not in st.session_state:
        st.session_state[k] = default
    return k


def call_get_prompt(template_path: str, **kwargs):
    """
    Primary parameter is max_characters (aligned with your script).
    If PromptOrchestrator expects max_words instead, fall back automatically.
    """
    try:
        return PromptOrchestrator.get_prompt(template_path, **kwargs)
    except TypeError:
        if "max_characters" in kwargs:
            alt = dict(kwargs)
            alt["max_words"] = alt.pop("max_characters")
            return PromptOrchestrator.get_prompt(template_path, **alt)
        raise


# App configuration
# ---------------------------------------------------------------------------------------------------------------
st.set_page_config(page_title="Prompt Viewer", layout="wide")

st.markdown(
    """
    <style>
      :root{
        --border: #e6edf5;
        --muted: #64748b;
        --text: #0f172a;
        --soft: #f8fafc;

        /* Sidebar blue palette */
        --sb-bg-top: #eaf2ff;
        --sb-bg-mid: #f5f9ff;
        --sb-bg-bottom: #ffffff;
        --sb-border: #cfe0ff;
        --sb-accent: #1d4ed8;
        --sb-accent-soft: rgba(29, 78, 216, 0.08);
        --sb-text: #0b2a6b;
      }

      .block-container { max-width: 1250px; padding-top: 1.25rem; padding-bottom: 2.25rem; }
      header[data-testid="stHeader"] { height: 0.35rem; }

      section[data-testid="stSidebar"] {
        border-right: 1px solid var(--sb-border);
        background: linear-gradient(180deg, var(--sb-bg-top) 0%, var(--sb-bg-mid) 55%, var(--sb-bg-bottom) 100%);
      }
      [data-testid="stSidebar"] .block-container { padding-top: 1.1rem; }

      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3 {
        color: var(--sb-text);
        letter-spacing: -0.01em;
      }
      [data-testid="stSidebar"] .stCaption { color: #27467b !important; }

      .stButton button { border-radius: 12px !important; padding: 0.55rem 0.85rem !important; }
      .stSelectbox div[data-baseweb="select"] > div { border-radius: 12px; }
      .stCheckbox { padding: 0.2rem 0; }

      [data-testid="stSidebar"] .stSelectbox label,
      [data-testid="stSidebar"] .stTextInput label,
      [data-testid="stSidebar"] .stCheckbox label {
        color: var(--sb-text) !important;
        font-weight: 600;
      }

      [data-testid="stSidebar"] details {
        border: 1px solid var(--sb-border);
        border-radius: 14px;
        background: rgba(29, 78, 216, 0.035);
        padding: 6px 10px;
      }
      [data-testid="stSidebar"] details summary { color: var(--sb-text); font-weight: 650; }

      .stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--border); }
      .stTabs [data-baseweb="tab"] { border-radius: 12px 12px 0 0; padding: 10px 12px; }
      .stTabs [aria-selected="true"] { background: white; border: 1px solid var(--border); border-bottom: 0; }

      .hero {
        border: 1px solid var(--border);
        background: linear-gradient(135deg, #f7f7ff 0%, #ffffff 40%, #f3fbff 100%);
        border-radius: 18px;
        padding: 18px 18px 14px 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
      }
      .hero-title { font-size: 1.55rem; font-weight: 750; color: var(--text); letter-spacing: -0.02em; margin-bottom: 4px; }
      .hero-subtitle { color: var(--muted); font-size: 0.98rem; margin-bottom: 10px; }
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
      .card-title { font-weight: 700; color: var(--text); margin-bottom: 6px; }
      .card-note { color: var(--muted); font-size: 0.92rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Paths / YAML
# ---------------------------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
base_fields = ROOT / "prompts" / "fields"

premises_candidates = [ROOT / "prompts" / "subfactors", ROOT / "prompts" / "premises"]
base_premises = next((p for p in premises_candidates if p.exists()), premises_candidates[0])

table_field_path = base_fields / "019_maturities.yaml"
macro_field_path = base_fields / "063_cfo_ir.yaml"
evaluation_info_path = base_premises / "question_17.yaml"

missing = [p for p in [table_field_path, macro_field_path, evaluation_info_path] if not p.exists()]
if missing:
    st.error("Missing required files:\n\n" + "\n".join([f"- {m}" for m in missing]))
    st.stop()

table_field = load_yaml(table_field_path)
macro_field = load_yaml(macro_field_path)
evaluation_info = load_yaml(evaluation_info_path)


# Template & parameter model
# ---------------------------------------------------------------------------------------------------------------
TEMPLATE_OPTIONS = [
    "Extract",
    "Critique",
    "Summarize",
    "Evaluate",
    "Consolidate",
    "User • Common",
]

FIELD_TYPE_OPTIONS = ["quantitative", "qualitative"]
MAX_CHARS_OPTIONS = [None, 300, 500, 800, 1000, 1500, 2000, 3000, 5000, 8000, 12000]

DEFAULTS = {
    # Extract (Quantitative)
    "Extract__quantitative": dict(
        output_language="es",
        max_characters=None,
        include_specifications=True,
        include_exclusions=True,
        include_synonyms=True,
        include_source_guides=True,
        include_normalization=True,
    ),
    # Extract (Qualitative)
    "Extract__qualitative": dict(
        output_language="es",
        max_characters=5000,
        include_source_guides=True,
        include_extraction_elements=True,
        include_traceability_rule=True,
        include_coverage_rule=True,
    ),

    # Critique (Quantitative)
    "Critique__quantitative": dict(
        output_language="es",
        max_characters=1000,
        include_specifications=True,
        include_exclusions=True,
    ),

    # Critique (Qualitative)
    "Critique__qualitative": dict(output_language="es", max_characters=1000),

    # Summarize
    "Summarize": dict(include_judgment=True, max_characters=1000),

    # Evaluation
    "Evaluate": dict(premise_id="strategic_planning", output_language="es", max_characters=1000),
    "Consolidate": dict(output_language="es", max_characters=2000),

    # User prompt
    "User • Common": dict(user_type="extract"),
}


# Session initialization
# ---------------------------------------------------------------------------------------------------------------
if "selected_template" not in st.session_state:
    st.session_state["selected_template"] = TEMPLATE_OPTIONS[0]


# Sidebar
# ---------------------------------------------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Configuration")

    st.selectbox(
        "Template",
        TEMPLATE_OPTIONS,
        key="selected_template",
        help="Template selection. For Extract and Critique, you can additionally filter by field type.",
    )

    selected_template = st.session_state["selected_template"]

    selected_field_type = None
    if selected_template in ("Extract", "Critique"):
        ft_key = f"selected_field_type__{sanitize_key(selected_template)}"
        if ft_key not in st.session_state:
            st.session_state[ft_key] = "quantitative"

        st.selectbox(
            "Field type",
            options=FIELD_TYPE_OPTIONS,
            key=ft_key,
            help="Select quantitative vs qualitative. This determines which YAML definition is applied.",
        )
        selected_field_type = st.session_state[ft_key]

    scope = scope_key(selected_template, selected_field_type)
    scope_defaults = DEFAULTS.get(scope, {})

    st.divider()
    st.caption("Parameters (applies only to the current selection)")

    # output_language
    if selected_template in ("Extract", "Critique", "Evaluate", "Consolidate"):
        k = ensure_state(scope, "output_language", scope_defaults.get("output_language", "es"))
        st.selectbox("Output language", options=["es", "en"], key=k)

    # max_characters
    if selected_template in ("Extract", "Critique", "Summarize", "Evaluate", "Consolidate"):
        k = ensure_state(scope, "max_characters", scope_defaults.get("max_characters", None))
        st.selectbox(
            "max_characters",
            options=MAX_CHARS_OPTIONS,
            key=k,
            format_func=lambda x: "No limit" if x is None else str(x),
            help="Character limit (as in the script).",
        )

    with st.expander("Advanced options", expanded=False):
        # Extract flags
        if selected_template == "Extract":
            if selected_field_type == "quantitative":
                k = ensure_state(scope, "include_specifications", scope_defaults.get("include_specifications", True))
                st.checkbox("include_specifications", key=k)

                k = ensure_state(scope, "include_exclusions", scope_defaults.get("include_exclusions", True))
                st.checkbox("include_exclusions", key=k)

                k = ensure_state(scope, "include_synonyms", scope_defaults.get("include_synonyms", True))
                st.checkbox("include_synonyms", key=k)

                k = ensure_state(scope, "include_source_guides", scope_defaults.get("include_source_guides", True))
                st.checkbox("include_source_guides", key=k)

                k = ensure_state(scope, "include_normalization", scope_defaults.get("include_normalization", True))
                st.checkbox("include_normalization", key=k)
            else:
                k = ensure_state(scope, "include_source_guides", scope_defaults.get("include_source_guides", True))
                st.checkbox("include_source_guides", key=k)

                k = ensure_state(scope, "include_extraction_elements", scope_defaults.get("include_extraction_elements", True))
                st.checkbox("include_extraction_elements", key=k)

                k = ensure_state(scope, "include_traceability_rule", scope_defaults.get("include_traceability_rule", True))
                st.checkbox("include_traceability_rule", key=k)

                k = ensure_state(scope, "include_coverage_rule", scope_defaults.get("include_coverage_rule", True))
                st.checkbox("include_coverage_rule", key=k)


        if selected_template == "Critique" and selected_field_type == "quantitative":
            k = ensure_state(scope, "include_specifications", scope_defaults.get("include_specifications", True))
            st.checkbox("include_specifications", key=k)

            k = ensure_state(scope, "include_exclusions", scope_defaults.get("include_exclusions", True))
            st.checkbox("include_exclusions", key=k)

        # Summarize
        if selected_template == "Summarize":
            k = ensure_state(scope, "include_judgment", scope_defaults.get("include_judgment", True))
            st.checkbox("include_judgment", key=k)

        # Evaluate
        if selected_template == "Evaluate":
            k = ensure_state(scope, "premise_id", scope_defaults.get("premise_id", "strategic_planning"))
            st.text_input("premise_id", key=k)

        # User prompt
        if selected_template == "User • Common":
            k = ensure_state(scope, "user_type", scope_defaults.get("user_type", "extract"))
            st.selectbox("user_type", options=["extract", "critique", "evaluate"], key=k)


def get_params(scope: str, param_names: list[str]) -> dict:
    out = {}
    defaults = DEFAULTS.get(scope, {})
    for p in param_names:
        out[p] = st.session_state.get(key_for(scope, p), defaults.get(p))
    return out


# Prompt build
# ---------------------------------------------------------------------------------------------------------------
def build_prompt(template_name: str, field_type: str | None) -> tuple[str, dict]:
    scope = scope_key(template_name, field_type)

    if template_name == "Extract":
        if field_type == "quantitative":
            params = get_params(
                scope,
                [
                    "output_language",
                    "max_characters",
                    "include_specifications",
                    "include_exclusions",
                    "include_synonyms",
                    "include_source_guides",
                    "include_normalization",
                ],
            )
            kwargs = {
                **table_field,
                "field_type": "quantitative",
                "output_language": params.get("output_language"),
                "max_characters": params.get("max_characters"),
                "include_specifications": params.get("include_specifications", True),
                "include_exclusions": params.get("include_exclusions", True),
                "include_synonyms": params.get("include_synonyms", True),
                "include_source_guides": params.get("include_source_guides", True),
                "include_normalization": params.get("include_normalization", True),
            }
            return call_get_prompt("extraction/extract", **kwargs), kwargs

        params = get_params(
            scope,
            [
                "output_language",
                "max_characters",
                "include_source_guides",
                "include_extraction_elements",
                "include_traceability_rule",
                "include_coverage_rule",
            ],
        )
        kwargs = {
            **macro_field,
            "field_type": "qualitative",
            "output_language": params.get("output_language"),
            "max_characters": params.get("max_characters"),
            "include_source_guides": params.get("include_source_guides", True),
            "include_extraction_elements": params.get("include_extraction_elements", True),
            "include_traceability_rule": params.get("include_traceability_rule", True),
            "include_coverage_rule": params.get("include_coverage_rule", True),
        }
        return call_get_prompt("extraction/extract", **kwargs), kwargs

    if template_name == "Critique":
        if field_type == "quantitative":
            params = get_params(scope, ["output_language", "max_characters", "include_specifications", "include_exclusions"])
            kwargs = {
                **table_field,
                "field_type": "quantitative",
                "output_language": params.get("output_language"),
                "max_characters": params.get("max_characters"),
                "include_specifications": params.get("include_specifications", True),
                "include_exclusions": params.get("include_exclusions", True),
            }
            return call_get_prompt("extraction/critique", **kwargs), kwargs

        params = get_params(scope, ["output_language", "max_characters"])
        kwargs = {
            **macro_field,
            "field_type": "qualitative",
            "output_language": params.get("output_language"),
            "max_characters": params.get("max_characters"),
        }
        return call_get_prompt("extraction/critique", **kwargs), kwargs

    if template_name == "Summarize":
        params = get_params(scope, ["include_judgment", "max_characters"])
        kwargs = {
            "include_judgment": params.get("include_judgment", True),
            "max_characters": params.get("max_characters"),
        }
        return call_get_prompt("extraction/summarize", **kwargs), kwargs

    if template_name == "Evaluate":
        params = get_params(scope, ["premise_id", "output_language", "max_characters"])
        kwargs = {
            **evaluation_info,
            "premise_id": params.get("premise_id", "strategic_planning"),
            "output_language": params.get("output_language"),
            "max_characters": params.get("max_characters"),
        }
        return call_get_prompt("evaluation/evaluate", **kwargs), kwargs

    if template_name == "Consolidate":
        params = get_params(scope, ["output_language", "max_characters"])
        kwargs = {
            **evaluation_info,
            "output_language": params.get("output_language"),
            "max_characters": params.get("max_characters"),
        }
        return call_get_prompt("evaluation/consolidate", **kwargs), kwargs

    if template_name == "User • Common":
        params = get_params(scope, ["user_type"])
        kwargs = {"user_type": params.get("user_type", "extract")}
        return call_get_prompt("common/user", **kwargs), kwargs

    raise ValueError(f"Unsupported template: {template_name}")


selected_template = st.session_state["selected_template"]
selected_field_type = None
if selected_template in ("Extract", "Critique"):
    ft_key = f"selected_field_type__{sanitize_key(selected_template)}"
    selected_field_type = st.session_state.get(ft_key, "quantitative")

content, used_kwargs = build_prompt(selected_template, selected_field_type)
html = md_to_html(content)


# UI
# ---------------------------------------------------------------------------------------------------------------
def chip_value(v):
    if v is None:
        return "No limit"
    if isinstance(v, bool):
        return "Yes" if v else "No"
    return str(v)

chips = [("Template", selected_template)]
if selected_template in ("Extract", "Critique"):
    chips.append(("Field type", selected_field_type))

for k in [
    "output_language",
    "max_characters",
    "premise_id",
    "include_judgment",
    "include_specifications",
    "include_exclusions",
    "include_synonyms",
    "include_source_guides",
    "include_normalization",
    "include_extraction_elements",
    "include_traceability_rule",
    "include_coverage_rule",
    "user_type",
]:
    if k in used_kwargs:
        chips.append((k, used_kwargs[k]))

word_count = len(content.split())

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-title">Prompt Viewer</div>
      <div class="hero-subtitle">Review prompts and adjust only the parameters exposed for the selected configuration.</div>
      {"".join([f'<span class="chip">{name}: <b>{chip_value(val)}</b></span>' for name, val in chips])}
      <span class="chip">Words (current): <b>{word_count}</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([3, 1])

with top_left:
    st.markdown(
        """
        <div class="card">
          <div class="card-title">Preview</div>
          <div class="card-note">Use the sidebar to switch templates and filter by field type where applicable.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    st.markdown(
        """
        <div class="card">
          <div class="card-title">Status</div>
          <div class="card-note">The prompt below reflects the current configuration.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

tab_md, tab_html, tab_raw = st.tabs(["Markdown", "HTML preview", "Raw"])

with tab_md:
    st.markdown(content)

with tab_html:
    components.html(html, height=720, scrolling=True)

with tab_raw:
    st.code(content, language="markdown")
