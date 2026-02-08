# app.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


# ======================================================================================
# Page config
# ======================================================================================
st.set_page_config(
    page_title="Rating Calculator - LLM Extraction",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ======================================================================================
# Styling (UI-only)
# ======================================================================================
def inject_css() -> None:
    st.markdown(
        """
<style>
:root{
  --bg0:#f7f9fd;
  --bg1:#eef4ff;
  --bg2:#ecfeff;

  --text:#0b1220;
  --muted:#516072;

  --brand:#001391;
  --brandDeep:#071a3a;
  --brandHi:#8fb3ff;
  --cyan:#06b6d4;

  --card: rgba(255,255,255,0.86);
  --border: rgba(2,6,23,0.10);

  --ok: #16a34a;
  --bad: #dc2626;
}

/* App background */
.stApp{
  background:
    radial-gradient(900px 520px at 12% 8%, rgba(0,19,145,0.12) 0%, rgba(0,19,145,0.00) 55%),
    radial-gradient(820px 520px at 88% 14%, rgba(6,182,212,0.10) 0%, rgba(6,182,212,0.00) 52%),
    linear-gradient(135deg, var(--bg0) 0%, var(--bg1) 52%, var(--bg2) 100%);
  color: var(--text);
}

/* Hide defaults */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Spacing */
.block-container { padding-top: 2.1rem; padding-bottom: 2rem; }
h1, h2, h3, h4 { letter-spacing: 0.2px; color: var(--text); }

/* Cards */
.card{
  background: var(--card);
  border: 1px solid rgba(0,19,145,0.12);
  border-radius: 18px;
  padding: 16px 16px 10px 16px;
  box-shadow: 0 14px 35px rgba(15,23,42,0.10);
  backdrop-filter: blur(10px);
  margin-bottom: 14px;
}
.card-title{
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  margin-bottom:10px;
}
.card-title .left{ font-weight: 850; font-size: 1.05rem; }

.badge{
  font-size: 0.78rem;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(0,19,145,0.08);
  color: var(--brand);
  border: 1px solid rgba(0,19,145,0.16);
}

/* Status pills */
.pill{
  font-size: 0.78rem;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(2,6,23,0.12);
  background: rgba(255,255,255,0.70);
  font-weight: 850;
}
.pill.ok{ color: var(--ok); border-color: rgba(22,163,74,0.25); background: rgba(22,163,74,0.10); }
.pill.bad{ color: var(--bad); border-color: rgba(220,38,38,0.25); background: rgba(220,38,38,0.10); }

/* Chips */
.chips{ display:flex; flex-wrap:wrap; gap:8px; margin-top:6px; }
.chip{
  display:inline-flex;
  align-items:center;
  padding:6px 10px;
  border-radius:999px;
  font-weight:800;
  font-size:0.80rem;
  color: rgba(6,18,44,.92);
  background: rgba(0,19,145,0.06);
  border: 1px solid rgba(0,19,145,0.14);
}

/* Buttons */
div[data-testid="stButton"]{ width: 190px !important; }
.stButton > button{
  width: 140px !important;
  height: 38px !important;
  padding: 0 12px !important;

  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;

  font-size: 0.90rem !important;
  line-height: 1 !important;
  border-radius: 10px !important;
  font-weight: 750 !important;

  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;

  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;

  background: linear-gradient(135deg,
    #071a3a 0%,
    #0b2a63 22%,
    #001391 44%,
    #8fb3ff 68%,
    #0a2aa6 85%,
    #071a3a 100%
  ) !important;

  border: 1px solid rgba(0, 19, 145, 0.35) !important;

  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.35),
    inset 0 -1px 0 rgba(0,0,0,0.18),
    0 12px 26px rgba(0, 19, 145, 0.18);

  text-shadow: 0 1px 0 rgba(0,0,0,0.22);
  transition: transform .12s ease, box-shadow .12s ease, filter .12s ease;

  position: relative !important;
  overflow: hidden !important;
}
.stButton > button:hover{
  transform: translateY(-1px);
  filter: brightness(1.03) contrast(1.02);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.38),
    inset 0 -1px 0 rgba(0,0,0,0.16),
    0 14px 30px rgba(0, 19, 145, 0.22);
}
.stButton > button:active{
  transform: translateY(0px);
  filter: brightness(0.99);
}

/* Ripple */
.stButton > button::after{
  content:"";
  position:absolute;
  inset:-40%;
  background: radial-gradient(circle at 50% 50%,
    rgba(255,255,255,0.65) 0%,
    rgba(255,255,255,0.22) 22%,
    rgba(255,255,255,0.00) 60%);
  opacity: 0;
  transform: scale(0.35);
  pointer-events:none;
}
.stButton > button:active::after{
  opacity: 1;
  transform: scale(1);
  animation: btnRipple .55s ease-out forwards;
}
@keyframes btnRipple{
  from{ opacity: .95; transform: scale(.35); }
  to  { opacity: 0;   transform: scale(1.10); }
}

/* Overlay loader */
.oai-overlay{
  position: fixed;
  inset: 0;
  z-index: 999999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(247,249,253,0.55);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  animation: overlayIn .18s ease-out;
}
@keyframes overlayIn{
  from{ opacity:0; transform: translateY(6px); }
  to{ opacity:1; transform: translateY(0); }
}
.oai-modal{
  width: 460px;
  max-width: 92vw;
  border-radius: 22px;
  padding: 18px 18px 16px 18px;
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(0,19,145,0.16);
  box-shadow: 0 40px 90px rgba(2,6,23,0.25);
  backdrop-filter: blur(12px);
  position: relative;
  overflow: hidden;
}
.oai-modal::before{
  content:"";
  position:absolute; left:0; top:0; right:0; height:3px;
  background: linear-gradient(90deg, rgba(0,19,145,1), rgba(143,179,255,.9), rgba(6,182,212,.65));
}
.oai-row{ display:flex; gap:14px; align-items:center; }
.oai-msg{ font-weight: 900; color: var(--text); font-size: 1.02rem; line-height: 1.15; }
.oai-sub{ margin-top: 2px; font-size: .88rem; color: rgba(81,96,114,.95); }
.oai-ring{
  width: 46px; height: 46px; border-radius: 999px;
  background: conic-gradient(from 90deg,
    rgba(0,19,145,0.00),
    rgba(143,179,255,0.95),
    rgba(6,182,212,0.85),
    rgba(0,19,145,0.00));
  -webkit-mask: radial-gradient(circle, transparent 58%, #000 59%);
          mask: radial-gradient(circle, transparent 58%, #000 59%);
  animation: ringSpin .85s linear infinite;
  filter: drop-shadow(0 10px 18px rgba(0,19,145,0.18));
}
@keyframes ringSpin{ to{ transform: rotate(360deg); } }
.oai-bar{
  margin-top: 14px;
  height: 8px;
  border-radius: 999px;
  background: rgba(2,6,23,0.06);
  overflow: hidden;
  border: 1px solid rgba(0,19,145,0.10);
}
.oai-bar > span{
  display:block;
  height: 100%;
  width: 45%;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(0,19,145,.95), rgba(143,179,255,.75), rgba(6,182,212,.65));
  animation: scanMove 1.05s ease-in-out infinite;
}
@keyframes scanMove{
  0%{ transform: translateX(-30%); opacity:.65; }
  50%{ transform: translateX(120%); opacity:1; }
  100%{ transform: translateX(220%); opacity:.65; }
}

/* Inputs */
.stTextInput input, .stTextArea textarea{
  border-radius: 12px !important;
  border: 1px solid rgba(148,163,184,0.40) !important;
  background: rgba(248,250,252,0.95) !important;
  color: var(--text) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus{
  outline: none !important;
  border: 1px solid rgba(0,19,145,0.45) !important;
  box-shadow: 0 0 0 4px rgba(0,19,145,0.12);
}

/* Alerts */
div[data-testid="stAlert"]{
  border-radius: 14px;
  border: 1px solid rgba(148,163,184,0.30);
  background: rgba(255,255,255,0.70);
}

/* Expander */
details{
  border-radius: 14px;
  border: 1px solid rgba(148,163,184,0.35);
  background: rgba(255,255,255,0.80);
  padding: 6px 10px;
}
details summary{ font-weight: 750; color: var(--text); }

/* Sidebar */
section[data-testid="stSidebar"] > div:first-child{
  background:
    radial-gradient(820px 520px at 18% 0%, rgba(0,19,145,0.18) 0%, rgba(0,19,145,0) 58%),
    radial-gradient(520px 380px at 80% 10%, rgba(6,182,212,0.10) 0%, rgba(6,182,212,0) 55%),
    linear-gradient(180deg,#eef2ff 0%,#e6edf7 55%,#dfe7f3 100%);
  border-right: 1px solid rgba(2,6,23,0.12);
  padding: 1.15rem 1.0rem 1.25rem;
  position: relative;
}
section[data-testid="stSidebar"] > div:first-child::before{
  content:"";
  position:absolute; left:0; top:0; bottom:0; width:4px;
  background: linear-gradient(180deg, rgba(0,19,145,1), rgba(143,179,255,.9), rgba(6,182,212,.55));
}
.sidebar-logo{ display:flex; align-items:center; gap:10px; padding: 0.2rem 0 0.8rem 0; }
.sidebar-logo img{ width:152px; max-width:100%; height:auto; display:block; object-fit:contain; }
.brand-chip{
  font-size: .75rem; font-weight: 900; color:#fff !important; -webkit-text-fill-color:#fff !important;
  background: linear-gradient(135deg,#071a3a 0%,#0b2a63 22%,#001391 44%,#8fb3ff 68%,#0a2aa6 85%,#071a3a 100%) !important;
  border:1px solid rgba(0,19,145,.35);
  padding:6px 12px; border-radius:999px; line-height:1; display:inline-flex; align-items:center;
  white-space:nowrap;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.35), inset 0 -1px 0 rgba(0,0,0,.18), 0 8px 18px rgba(0,19,145,.18);
  text-shadow:0 1px 0 rgba(0,0,0,.22);
}
.sidebar-card{
  background: rgba(0,19,145,0.045);
  border: 1px solid rgba(0,19,145,0.14);
  border-radius: 18px;
  padding: 14px 14px 12px 14px;
  box-shadow: 0 10px 24px rgba(2,6,23,0.04);
  position: relative;
  overflow: hidden;
}
.sidebar-card::before{
  content:"";
  position:absolute; left:0; top:0; right:0; height:3px;
  background: linear-gradient(90deg, rgba(0,19,145,.95), rgba(143,179,255,.55), rgba(0,19,145,0));
}
.sidebar-title{ font-weight: 900; font-size: 0.95rem; margin-bottom: 4px; }
.sidebar-muted{ font-size: 0.82rem; color: rgba(6,18,44,.68); }
</style>
""",
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
<div style="display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:12px;">
  <div>
    <div style="color:#0b1220;font-weight:900;font-size:1.85rem;line-height:1.1;">
      RATING CALCULATOR — LLM Field Extraction
    </div>
    <div style="color:rgba(81,96,114,.95);font-weight:700;">
      Initial extraction • Alternative extraction • Critique
    </div>
  </div>
  <div style="
      padding:8px 12px;
      border-radius:999px;
      background:rgba(255,255,255,0.70);
      border:1px solid rgba(2,6,23,0.10);
      backdrop-filter:blur(10px);
      color:#0b1220;
      font-weight:800;">
    BBVA AI Lab
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


@contextmanager
def card(title: str, badge: str) -> Any:
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">
    <div class="left">{title}</div>
    <div class="badge">{badge}</div>
  </div>
""",
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)


# ======================================================================================
# Overlay helpers
# ======================================================================================
overlay_slot = st.empty()

OVERLAY_HTML = """
<div class="oai-overlay">
  <div class="oai-modal">
    <div class="oai-row">
      <div class="oai-ring"></div>
      <div>
        <div class="oai-msg">{msg}</div>
        <div class="oai-sub">Processing request (LLM)…</div>
      </div>
    </div>
    <div class="oai-bar"><span></span></div>
  </div>
</div>
"""


@contextmanager
def busy(msg: str) -> Any:
    overlay_slot.markdown(OVERLAY_HTML.format(msg=msg), unsafe_allow_html=True)
    try:
        yield
    finally:
        overlay_slot.empty()


# ======================================================================================
# Helpers (data normalization + rendering)
# ======================================================================================
def first_sentence(text: str, fallback_len: int = 180) -> str:
    if not text:
        return ""
    t = re.sub(r"\s+", " ", str(text).strip())
    m = re.search(r"^(.+?[.!?])(\s|$)", t)
    if m:
        return m.group(1)
    return t[:fallback_len] + ("…" if len(t) > fallback_len else "")


def as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except Exception:
            return {"raw": obj}
    return {"raw": str(obj)}


def result_to_dataframe(result_field: Dict[str, Any]) -> Optional[pd.DataFrame]:
    if not isinstance(result_field, dict):
        return None

    # Table schema: {columns: [...], rows: [[...], ...]}
    if "columns" in result_field and "rows" in result_field:
        cols = result_field.get("columns") or []
        rows = result_field.get("rows") or []
        try:
            return pd.DataFrame(rows, columns=cols)
        except Exception:
            return pd.DataFrame(rows)

    # Numeric schema: {value: ..., unit: ..., currency: ...}
    if "value" in result_field:
        return pd.DataFrame(
            [
                {
                    "value": result_field.get("value"),
                    "unit": result_field.get("unit"),
                    "currency": result_field.get("currency"),
                }
            ]
        )

    return None


def render_result_box(response: Dict[str, Any]) -> None:
    result_field = response.get("result_field") or {}
    df = result_to_dataframe(result_field)

    # Numeric/Table -> dataframe
    if df is not None:
        st.dataframe(df, use_container_width=True, hide_index=True)
        return

    # String -> text box
    text = ""
    if isinstance(result_field, dict) and "text" in result_field:
        text = result_field.get("text") or ""
    st.text_area(
        "LLM Output",
        value=str(text),
        height=220,
        label_visibility="collapsed",
        placeholder="No text output available…",
        key=f"ta_{hash(json.dumps(response, default=str))}",
    )


def render_sources_block(text_sources: List[Dict[str, Any]]) -> None:
    if not text_sources:
        st.info("No sources available.")
        return

    # Use styled HTML <details> (already themed in CSS)
    for i, src in enumerate(text_sources, start=1):
        doc = src.get("chunk_document", "—")
        pages = src.get("chunk_page") or []
        pages_str = ", ".join(map(str, pages)) if pages else "—"
        chunk_id = src.get("chunk_id", "—")
        sentence = first_sentence(src.get("text", "")) or "—"

        st.markdown(
            f"""
<details>
  <summary>{i}. <b>{doc}</b> — pages: {pages_str}</summary>
  <div style="padding:8px 6px 2px 6px;">
    <div style="margin-bottom:6px;"><b>Snippet:</b> {sentence}</div>
    <div style="color:rgba(81,96,114,.95); font-weight:700;">
      <span style="display:inline-block; margin-right:10px;"><b>chunk_id</b>: <code>{chunk_id}</code></span>
      <span><b>pages</b>: {pages_str}</span>
    </div>
  </div>
</details>
""",
            unsafe_allow_html=True,
        )


def render_justification_and_synonyms(response: Dict[str, Any]) -> None:
    justification = response.get("justification") or ""
    synonyms = response.get("synonyms_found") or []

    st.text_area(
        "Justification",
        value=str(justification),
        height=160,
        label_visibility="collapsed",
        key=f"ta_j_{hash(str(justification))}",
    )

    if synonyms:
        chips = "".join([f"<span class='chip'>{st._utils.escape_markdown(str(s))}</span>" for s in synonyms])
        # escape_markdown is fine for basic safety; we still render HTML for layout
        st.markdown(f"<div class='chips'>{chips}</div>", unsafe_allow_html=True)
    else:
        st.caption("No synonyms found.")


def render_critique_block(critique: Dict[str, Any]) -> None:
    if not critique:
        st.info("No critique available.")
        return

    is_valid = bool(critique.get("is_valid"))
    confidence = critique.get("confidence")
    justification = critique.get("justification") or ""

    pill_class = "ok" if is_valid else "bad"
    pill_text = "VALID" if is_valid else "NOT VALID"

    left, right = st.columns([1, 2], gap="large")
    with left:
        st.markdown(f"<span class='pill {pill_class}'>{pill_text}</span>", unsafe_allow_html=True)
        if isinstance(confidence, (int, float)):
            st.caption("Confidence")
            st.progress(min(max(float(confidence), 0.0), 1.0))
        else:
            st.caption("Confidence: —")

    with right:
        st.text_area(
            "Critique justification",
            value=str(justification),
            height=140,
            label_visibility="collapsed",
            key=f"ta_c_{hash(str(justification))}",
        )


# ======================================================================================
# Backend (logic-only)
# ======================================================================================
LANGUAGE = "ES"
PROMPTS_SUBMODULE = "prompts-data_research-aigenpf"
CATALOG_XLSX = "DS - Campos prioritarios.xlsx"
CATALOG_SHEET = "Inventario campos"

all_indexes = {
    "repsol": [
        ["repsol_cuentas-anuales-consolidadas_dump"],
        ["repsol_cuentas-anuales-informe-gestion-individual_dump"],
        ["repsol_informacion-actividades-exploracion-produccion-hidrocarburos-2024_dump"],
        ["repsol_informacion-publica-periodica-2024_dump"],
        ["repsol_informe-anual-gobierno-corporativo_dump"],
        ["repsol_informe-anual-remuneraciones-consejeros_dump"],
        ["repsol_informe-financiero-anual-consolidado_dump"],
        ["repsol_informe-financiero-anual-individual_dump"],
        ["repsol_informe-gestion-consolidado-2024_dump"],
        ["repsol_informe-pagos-administraciones-publicas-actividades-exploracion-produccion-hidrocarburos_dump"],
        ["repsol_ip22022024-presentacion-resultados-cuarto-trimestre-ejercicio-2023-actualizacion-estrategica-2024-2027_dump"],
        ["repsol_politica-financiera-final_es_dump"],
        ["repsol_ratings-crediticios-14-20_dump"],
    ],
    "acciona": [
        ["acciona_esp_informe_resultados_2024_textract"],
        ["acciona_esp_memoria_anual_2024_textract"],
        ["acciona_esp_memoria_anual_integrada_2024_textract"],
        ["acciona_esp_memoria_semestral_2025_s1_textract"],
        ["acciona_esp_memoria_sostenibilidad_2024_textract"],
        ["acciona_esp_memoria_trimestral_2025_q2_textract"],
        ["acciona_esp_programa_financiero_2024_10_textract"],
    ],
    "dia": [
        ["dia_esp_plan_estrategico_2025_textract"],
        ["dia_esp_boe_reduccion_capital_2025_textract"],
        ["dia_esp_cmd_presentation_2025_textract"],
        ["dia_esp_memoria_anual_integrada_2024_textract"],
        ["dia_esp_memoria_semestral_2025_s1_textract"],
        ["dia_esp_nota_nueva_estructura_2024_textract"],
        ["dia_esp_programa_financiero_2024_textract"],
    ],
}

BACKEND_AVAILABLE = True
try:
    from aigenpf.application.prompt.prompt_reader import PromptReaderFromRepo
    from aigenpf.application.prompt.yaml_loader import LocalYamlLoader
    from aigenpf.application.retrieval_component.retrieval_component import RetrieveComponent

    from aigenrc.llm import RatingCalculatorLm
    from aigenrc.utils import (
        OutputNumericField,
        OutputSchemaCritic,
        OutputStringField,
        OutputTableField,
        get_critique_prompt_with_context,
        get_extract_prompt_with_context,
    )
except Exception:
    BACKEND_AVAILABLE = False


@st.cache_resource
def get_backend_objects() -> Dict[str, Any]:
    if not BACKEND_AVAILABLE:
        return {}

    yaml_loader = LocalYamlLoader(prompts_submodule=PROMPTS_SUBMODULE, language=LANGUAGE)
    prompt_loader = PromptReaderFromRepo(yaml_loader)

    retrieve_component = RetrieveComponent(top_k=20)

    text_llm = RatingCalculatorLm(output_schema=OutputStringField)
    table_llm = RatingCalculatorLm(output_schema=OutputTableField)
    numeric_llm = RatingCalculatorLm(output_schema=OutputNumericField)
    critic_llm = RatingCalculatorLm(output_schema=OutputSchemaCritic)

    retrieve_params_df = prompt_loader.params["retrieve"].copy().reset_index(drop=True)

    return {
        "prompt_loader": prompt_loader,
        "retrieve_params_df": retrieve_params_df,
        "retrieve_component": retrieve_component,
        "text_llm": text_llm,
        "table_llm": table_llm,
        "numeric_llm": numeric_llm,
        "critic_llm": critic_llm,
    }


@st.cache_data
def build_registry_for_company(company: str, retrieve_params_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_indexes = pd.Series(all_indexes[company], name="index_name")

    df_aux = (
        retrieve_params_df.copy()
        .reset_index(drop=True)
        .sort_values(by=["fieldId"])
    )
    df_aux = df_aux.merge(df_indexes, how="cross").reset_index(drop=True)
    df_aux["field_id"] = df_aux["fieldId"] + "_" + df_aux["subfield"]

    fields_info = df_aux[["field", "field_id"]].drop_duplicates().reset_index(drop=True)

    # Merge catalog for field type (Numeric / Table / String)
    try:
        catalog = pd.read_excel(CATALOG_XLSX, sheet_name=CATALOG_SHEET)[
            ["Alias Campo (YAML y Catálogo MLEs)", "Tipo"]
        ]
        catalog.columns = ["field", "type"]
        fields_info = pd.merge(fields_info, catalog, how="left", on="field")
    except Exception:
        fields_info["type"] = "String"

    fields_info["type"] = fields_info["type"].fillna("String")
    return df_aux, fields_info


def pick_schema_and_llm(field_type: str, backend: Dict[str, Any]):
    field_type_norm = (field_type or "").strip().lower()
    if field_type_norm == "numeric":
        return OutputNumericField, backend["numeric_llm"]
    if field_type_norm == "table":
        return OutputTableField, backend["table_llm"]
    return OutputStringField, backend["text_llm"]


def retrieve_chunks(company: str, df_aux: pd.DataFrame, field_id: str, backend: Dict[str, Any]) -> pd.DataFrame:
    df_fields = df_aux[df_aux["field_id"] == field_id].copy()
    df_fields["language"] = LANGUAGE
    df_fields["prompt_language"] = LANGUAGE

    indexes = pd.Series(all_indexes[company], name="index_name").to_list()
    return backend["retrieve_component"].retrieve(index_names=indexes, df_fields=df_fields)


def extract_with_prompt(
    df_retrieved: pd.DataFrame,
    field_id: str,
    prompt_suffix: str,
    output_schema: Any,
    llm: Any,
) -> Any:
    prompt = f"{field_id}/{field_id}_{prompt_suffix}"
    system_prompt, user_prompt = get_extract_prompt_with_context(prompt, df_retrieved, 10)
    raw = llm.llm_response(system_prompt, user_prompt)
    return output_schema.model_validate_json(raw)


def critique_with_prompt(
    df_retrieved: pd.DataFrame,
    field_id: str,
    field_extract_obj: Any,
    backend: Dict[str, Any],
) -> Any:
    prompt = f"{field_id}/{field_id}_critique"
    system_prompt, user_prompt = get_critique_prompt_with_context(prompt, df_retrieved, 10, field_extract_obj)
    raw = backend["critic_llm"].llm_response(system_prompt, user_prompt)
    return OutputSchemaCritic.model_validate_json(raw)


def run_pipeline(company: str, field_id: str, field_type: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    backend = get_backend_objects()
    if not backend:
        # Minimal mock fallback (keeps UI usable if backend deps are missing)
        example_numeric = {
            "text_source": [{"text": "Example source…", "chunk_id": "chunk_1", "chunk_document": "doc.pdf", "chunk_page": [1]}],
            "justification": "Backend not available: showing mock payload.",
            "synonyms_found": ["mock", "example"],
            "result_field": {"value": 54000000, "unit": None, "currency": "EUR"},
        }
        example_table = {
            "text_source": [{"text": "Example source…", "chunk_id": "chunk_1", "chunk_document": "doc.pdf", "chunk_page": [1]}],
            "justification": "Backend not available: showing mock payload.",
            "synonyms_found": ["mock", "example"],
            "result_field": {"columns": ["metric", "value"], "rows": [["x", 1], ["y", 2]]},
        }
        example_text = {
            "text_source": [{"text": "Example source…", "chunk_id": "chunk_1", "chunk_document": "doc.pdf", "chunk_page": [1]}],
            "justification": "Backend not available: showing mock payload.",
            "synonyms_found": ["mock", "example"],
            "result_field": {"text": "Mock text output."},
        }
        critique = {"is_valid": False, "confidence": 0.0, "justification": "Backend not available."}

        ft = (field_type or "").lower()
        base = example_numeric if ft == "numeric" else example_table if ft == "table" else example_text
        return base, base, critique

    df_aux, _ = build_registry_for_company(company, backend["retrieve_params_df"])
    schema, llm = pick_schema_and_llm(field_type, backend)

    df_retrieved = retrieve_chunks(company, df_aux, field_id, backend)

    initial_obj = extract_with_prompt(df_retrieved, field_id, "extract", schema, llm)
    alternative_obj = extract_with_prompt(df_retrieved, field_id, "alternative", schema, llm)
    critique_obj = critique_with_prompt(df_retrieved, field_id, initial_obj, backend)

    return as_dict(initial_obj), as_dict(alternative_obj), as_dict(critique_obj)


# ======================================================================================
# Session state
# ======================================================================================
for k, v in {
    "initial": {},
    "alternative": {},
    "critique": {},
    "selected_company": None,
    "selected_field_id": None,
    "selected_field_type": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ======================================================================================
# UI
# ======================================================================================
inject_css()
render_header()

LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/BBVA_logo_2025.svg/2560px-BBVA_logo_2025.svg.png"

with st.sidebar:
    st.markdown(
        f"""
<div class="sidebar-logo">
  <img src="{LOGO_URL}" alt="Logo" />
  <span class="brand-chip">RATING<br>CALCULATOR</span>
</div>

<div class="sidebar-card">
  <div class="sidebar-title">Configuration</div>
  <div class="sidebar-muted">Filter by company and field.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    company = st.selectbox("Company", list(all_indexes.keys()), key="sb_company")
    field_search = st.text_input("Field filter", placeholder="Type to filter fields…", key="sb_field_search")

    if BACKEND_AVAILABLE:
        backend = get_backend_objects()
        df_aux, fields_info = build_registry_for_company(company, backend["retrieve_params_df"])
    else:
        fields_info = pd.DataFrame(
            [{"field": "example_field", "field_id": "example_id_sub", "type": "String"}]
        )

    filtered = fields_info.copy()
    if field_search.strip():
        q = field_search.strip().lower()
        filtered = filtered[filtered["field"].str.lower().str.contains(q, na=False)]

    # Build select labels
    options = filtered.to_dict("records")
    if not options:
        st.warning("No fields match the filter.")
        selected = {"field": "", "field_id": "", "type": "String"}
    else:
        labels = [f"{r['field']}  •  {r['field_id']}  •  {r.get('type','String')}" for r in options]
        idx = st.selectbox("Field", list(range(len(labels))), format_func=lambda i: labels[i], key="sb_field_idx")
        selected = options[idx]

    st.markdown("---")
    run_clicked = st.button("Run extraction", key="btn_run")

# Run pipeline
if run_clicked and selected.get("field_id"):
    with busy("Running extraction…"):
        initial, alternative, critique = run_pipeline(company, selected["field_id"], selected.get("type", "String"))

    st.session_state.initial = initial
    st.session_state.alternative = alternative
    st.session_state.critique = critique
    st.session_state.selected_company = company
    st.session_state.selected_field_id = selected["field_id"]
    st.session_state.selected_field_type = selected.get("type", "String")

# Show warning if backend missing
if not BACKEND_AVAILABLE:
    st.warning("Backend imports not available. UI is running in mock mode.")


# ======================================================================================
# Vertical layout (all sections stacked)
# ======================================================================================
field_meta = f"Company: {st.session_state.selected_company or '—'} | Field: {st.session_state.selected_field_id or '—'} | Type: {st.session_state.selected_field_type or '—'}"
st.caption(field_meta)

# --- Stage 1: Initial extraction
with card("1) Initial extraction — Output", "Extract"):
    if st.session_state.initial:
        render_result_box(st.session_state.initial)
    else:
        st.info("Run an extraction to display the initial output.")

with card("1) Initial extraction — Text sources", "Sources"):
    render_sources_block((st.session_state.initial or {}).get("text_source") or [])

with card("1) Initial extraction — Justification & synonyms", "Explain"):
    if st.session_state.initial:
        render_justification_and_synonyms(st.session_state.initial)
    else:
        st.info("Run an extraction to display justification and synonyms.")

# --- Stage 2: Alternative extraction
with card("2) Alternative extraction — Output", "Alternative"):
    if st.session_state.alternative:
        render_result_box(st.session_state.alternative)
    else:
        st.info("Run an extraction to display the alternative output.")

with card("2) Alternative extraction — Text sources", "Sources"):
    render_sources_block((st.session_state.alternative or {}).get("text_source") or [])

with card("2) Alternative extraction — Justification & synonyms", "Explain"):
    if st.session_state.alternative:
        render_justification_and_synonyms(st.session_state.alternative)
    else:
        st.info("Run an extraction to display justification and synonyms.")

# --- Critique
with card("3) Critique", "Critique"):
    render_critique_block(st.session_state.critique or {})
