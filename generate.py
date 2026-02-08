# -*- coding: utf-8 -*-

# =========================
# Modules
# =========================
import streamlit as st
import re
from contextlib import contextmanager
import os

import pandas as pd
import yaml

import json
from pathlib import Path
import time

from aigenpf.application.prompt.prompt_reader import PromptReaderFromRepo
from aigenpf.application.prompt.yaml_loader import LocalYamlLoader
from aigenpf.application.retrieval_component.retrieval_component import (
    RetrieveComponent,
)

from aigenrc.llm import RatingCalculatorLm
from aigenrc.utils import (
    OutputStringField,
    OutputTableField,
    OutputNumericField,
    OutputSchemaCritic,
    get_critique_prompt_with_context,
    get_extract_prompt_with_context,
    get_summary_prompt_from_text,
)

# =========================
# Load prompt
# =========================
LANGUAGE = "ES"
PROMPTS_SUBMODULE = (
    "prompts-data_research-aigenpf",
)

yaml_loader = LocalYamlLoader(prompts_submodule=PROMPTS_SUBMODULE, language=LANGUAGE)
prompt_loader = PromptReaderFromRepo(yaml_loader)

# =========================
# Chunks reference
# =========================
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

# =========================
# Auxiliar df
# =========================
company_list = list(all_indexes.keys())

COMPANY = company_list[0]

df_indexes = pd.Series(all_indexes[COMPANY], name="index_name")

df_aux = (
    prompt_loader.params["retrieve"]
    .copy()
    .reset_index(drop=True)
    .sort_values(by=["fieldId"])
)

df_aux = df_aux.merge(df_indexes, how="cross")
df_aux = df_aux.reset_index(drop=True)
df_aux["field_id"] = df_aux["fieldId"] + "_" + df_aux["subfield"]

fields_info = df_aux[["field", "field_id"]].drop_duplicates().reset_index(drop=True)
fields_info

# =========================
# Fields catalog merge
# =========================
fields_catalog = pd.read_excel(
    "DS - Campos prioritarios.xlsx",
    sheet_name="Inventario campos",
)[["Alias Campo (YAML y Catálogo MLEs)", "Tipo"]]

fields_catalog.columns = ["field", "type"]
fields_info = pd.merge(fields_info, fields_catalog, how="left")
fields_info

# =========================
# Field params
# =========================
idx = 1

field = fields_info.iloc[idx]["field"]
field_id = fields_info.iloc[idx]["field_id"]
field_type = fields_info.iloc[idx]["type"]

# =========================
# Common classes
# =========================
top_k_retrieve = 20
top_k_extract = 10

retrieve_component = RetrieveComponent(top_k=top_k_retrieve)

text_extract_llm = RatingCalculatorLm(output_schema=OutputStringField)
table_extract_llm = RatingCalculatorLm(output_schema=OutputTableField)
numeric_extract_llm = RatingCalculatorLm(output_schema=OutputNumericField)
field_critique_llm = RatingCalculatorLm(output_schema=OutputSchemaCritic)
summary_llm = RatingCalculatorLm(output_schema = None)


def retrieved_chunks(field):
    # Select the field you want to compute
    fields = df_aux[df_aux["field"] == field].copy()
    indexes = df_indexes.to_list()
    fields["language"] = LANGUAGE
    fields["prompt_language"] = LANGUAGE

    df_retrieved = retrieve_component.retrieve(index_names=indexes, df_fields=fields)

    return df_retrieved


def extract_field(df_retrieved, field_id, output_schema):
    prompt = f"{field_id}/{field_id}_extract"
    system_prompt, user_prompt = get_extract_prompt_with_context(
        prompt, df_retrieved, top_k_extract
    )

    field_extract_raw = table_extract_llm.llm_response(system_prompt, user_prompt)
    field_extract_sch = output_schema.model_validate_json(field_extract_raw)
    field_extract_res = field_extract_sch.model_dump_json(indent=4)
    print(field_extract_res)

    return field_extract_sch


def extract_alternative_field(df_retrieved, field_id, output_schema):
    prompt = f"{field_id}/{field_id}_alternative"
    system_prompt, user_prompt = get_extract_prompt_with_context(
        prompt, df_retrieved, top_k_extract
    )

    field_extract_raw = table_extract_llm.llm_response(system_prompt, user_prompt)
    field_extract_sch = output_schema.model_validate_json(field_extract_raw)
    field_extract_res = field_extract_sch.model_dump_json(indent = 4)
    print(field_extract_res)

    return field_extract_sch


def summary(text):
    prompt = "summary_prompts/general_conclusion"
    text = text.model_dump().get("result_field").get("text")

    system_prompt, user_prompt = get_summary_prompt_from_text(
        prompt,
        text,
    )

    plan_extract_raw = summary_llm.llm_response(system_prompt, user_prompt)

    return plan_extract_raw


def critique_field(df_retrieved, field_id, field_extract_sch):
    prompt = f"{field_id}/{field_id}_critique"
    system_prompt, user_prompt = get_critique_prompt_with_context(
        prompt, df_retrieved, top_k_extract, field_extract_sch
    )

    print("Initial extraction was successful. Let's autoevaluate the value...")
    field_critique_raw = field_critique_llm.llm_response(system_prompt, user_prompt)
    field_critique_sch = OutputSchemaCritic.model_validate_json(field_critique_raw)
    field_critique_res = field_critique_sch.model_dump_json(indent = 4)
    print(field_critique_res)

    return field_critique_sch




df_retrieved = retrieved_chunks(field=field)

if field_type == "Numeric":
    output_schema = OutputNumericField
elif field_type == "Table":
    output_schema = OutputTableField
else:
    output_schema = OutputStringField

# =========================
# Extract
# =========================
response_extract = extract_field(
    df_retrieved=df_retrieved,
    field_id=field_id,
    output_schema=output_schema,
)

if field_type != "String":
    # Alternative
    response_alternative = extract_alternative_field(
        df_retrieved=df_retrieved,
        field_id=field_id,
        output_schema=output_schema,
    )

if field_type == "String":
    field_summary = summary(response_extract)

# =========================
# Critique
# =========================
response_critique = critique_field(
    df_retrieved=df_retrieved,
    field_id=field_id,
    field_extract_sch=response_extract,
)

# Ejemplo de output tabla:
{
  "text_source": [
    {
      "text": "A parallel upward shift of +25 bps would decrease profit or loss by EUR 21.0 million ...",
      "chunk_id": "chunk_57",
      "chunk_document": "Annual Report 2023.pdf",
      "chunk_page": [
        95,
        96
      ]
    },
    {
      "text": "Market risk – interest rate risk: sensitivity (P\u0026L) for +25 bps: (EUR 21.0 million) ...",
      "chunk_id": "chunk_12",
      "chunk_document": "Annual Report 2023.pdf",
      "chunk_page": [
        140
      ]
    }
  ],
  "justification": "Se toma el escenario positivo (+) del análisis de sensibilidad de tipos y su impacto en P\u0026L. Se registran ambos componentes (shock y efecto monetario) y se excluye equity/OCI...\n",
  "synonyms_found": [
    "interest rate sensitivity",
    "profit or loss",
    "bps",
    "..."
  ],
  "result_field": {
    "columns": [
      "metric",
      "value",
      "unit",
      "currency"
    ],
    "rows": [
      [
        "ir_stress_value",
        "25",
        "pct",
        ""
      ],
      [
        "ir_stress_pl",
        "-21000000",
        "",
        "EUR"
      ]
    ]
  }
}

# Ejmemplot de output numerico:
{
  "text_source": [
    {
      "text": "Unhedged foreign-currency debt at year-end amounted to EUR 54.0 million ...",
      "chunk_id": "chunk_12",
      "chunk_document": "Annual Report 2023.pdf",
      "chunk_page": [
        14,
        15
      ]
    },
    {
      "text": "Uncovered foreign-currency debt (without hedging) at year-end: EUR 54.0 million ...",
      "chunk_id": "chunk_13",
      "chunk_document": "Annual Report 2023.pdf",
      "chunk_page": [
        13
      ]
    }
  ],
  "justification": "El texto identifica explícitamente deuda en moneda extranjera sin cobertura al cierre. Se extrae el importe reportado...\n",
  "synonyms_found": [
    "unhedged foreign-currency debt",
    "uncovered foreign-currency debt",
    "..."
  ],
  "result_field": {
    "value": 54000000,
    "unit": null,
    "currency": "EUR"
  }
}

# Ejemplo de output string:
{
  "result_field": {
    "text": "Sensibilidad moderada del CFO a tipos, principalmente indirecta vía indexación a IPC/HICP y efectos en capital circulante; impacto directo limitado por pass-through regulatorio, además ..."
  },
  "text_source": [
    {
      "text": "Regulated revenues are indexed to CPI (HICP) with an annual adjustment and a lag; true-up mechanism applies and ...",
      "chunk_id": "chunk_000812",
      "chunk_document": "AnnualReport_2024_EN",
      "chunk_page": [
        132
      ]
    },
    {
    "text_source": "...",
    }
  ],
  "justification": "Se infiere sensibilidad indirecta (indexación IPC/HICP) y limitada directa (pass-through regulatorio) ...",
  "synonyms_found": [
    "sensibilidad a tipos de interés",
    "IPC/HICP",
    "pass-through",
    "capital circulante"
  ]
}

# Estrcutura critique:
{
    "is_valid": bool,     
    "confidence": float, 
    "justification": str
}



import json
import pandas as pd

try:
    from IPython.display import display
except ImportError:
    display = None


def _show_df(df: pd.DataFrame, title: str = ""):
    if title:
        print(f"\n== {title} ==")
    if display:
        display(df)
    else:
        print(df.to_string(index=False))


def _show_text(title: str, text: str):
    print(f"\n== {title} ==")
    print(text if text is not None else "")


def show_output(data):
    """
    data puede ser:
      - dict
      - string con JSON
      - lista de dicts (muestra como DataFrame si procede)
    """
    if isinstance(data, str):
        data = json.loads(data)

    if isinstance(data, list):
        # Si es una lista de dicts, intento DataFrame directo
        if all(isinstance(x, dict) for x in data):
            _show_df(pd.DataFrame(data), "lista")
        else:
            print(data)
        return

    if not isinstance(data, dict):
        print(data)
        return

    # Caso "critique" exacto
    if set(data.keys()) == {"is_valid", "confidence", "justification"}:
        _show_df(pd.DataFrame([{"is_valid": data["is_valid"], "confidence": data["confidence"]}]), "critique")
        _show_text("justification", data["justification"])
        return

    # 1) result_field (tabla / numérico / texto)
    rf = data.get("result_field")
    if isinstance(rf, dict):
        if "columns" in rf and "rows" in rf:
            df = pd.DataFrame(rf["rows"], columns=rf["columns"])
            _show_df(df, "result_field (tabla)")
        elif "value" in rf:
            _show_df(pd.DataFrame([rf]), "result_field (numérico)")
        elif "text" in rf:
            _show_text("result_field (texto)", rf.get("text", ""))
        else:
            # fallback: dict cualquiera -> df de una fila
            _show_df(pd.DataFrame([rf]), "result_field")
    elif rf is not None:
        # fallback: result_field primitivo
        _show_df(pd.DataFrame([{"value": rf}]), "result_field")

    # 2) justification (texto normal)
    if "justification" in data:
        _show_text("justification", data.get("justification", ""))

    # 3) synonyms_found (lista legible)
    if "synonyms_found" in data:
        syn = data.get("synonyms_found") or []
        print("\n== synonyms_found ==")
        if isinstance(syn, list):
            for s in syn:
                print(f"- {s}")
        else:
            print(syn)

    # 4) text_source (texto normal, sin truncar)
    if "text_source" in data:
        ts = data.get("text_source") or []
        print("\n== text_source ==")
        if isinstance(ts, list) and all(isinstance(x, dict) for x in ts):
            for i, x in enumerate(ts, 1):
                doc = x.get("chunk_document")
                cid = x.get("chunk_id")
                pages = x.get("chunk_page")
                pages_str = ", ".join(map(str, pages)) if isinstance(pages, list) else str(pages)
                print(f"\n[{i}] {doc} | {cid} | page(s): {pages_str}")
                print(x.get("text", ""))
        else:
            print(ts)


import json, html
import pandas as pd

try:
    from IPython.display import display, HTML
except ImportError:
    display = None


def show_output(data):
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, dict):
        print(data); return

    def show_text(title, text, open=False):
        text = "" if text is None else str(text)
        if display:
            display(HTML(f"""
            <details{" open" if open else ""} style="margin:.4rem 0;">
              <summary style="cursor:pointer;font-weight:600;">{html.escape(title)}</summary>
              <pre style="white-space:pre-wrap;margin:.5rem 0 0 0;">{html.escape(text)}</pre>
            </details>
            """))
        else:
            print(f"\n== {title} ==\n{text}")

    def show_list(title, items):
        if items is None: items = []
        if not isinstance(items, list): items = [items]
        if display:
            lis = "".join(f"<li>{html.escape(str(x))}</li>" for x in items)
            display(HTML(f"<div style='margin:.6rem 0;font-weight:700;'>{html.escape(title)}</div><ul style='margin-top:.2rem'>{lis}</ul>"))
        else:
            print(f"\n== {title} ==")
            for x in items: print(f"- {x}")

    def show_df(df, title=""):
        if title: print(f"\n== {title} ==")
        (display(df) if display else print(df.to_string(index=False)))

    # critique
    if set(data.keys()) == {"is_valid", "confidence", "justification"}:
        show_df(pd.DataFrame([{"is_valid": data["is_valid"], "confidence": data["confidence"]}]), "critique")
        show_text("justification", data["justification"])
        return

    # result_field
    rf = data.get("result_field")
    if isinstance(rf, dict):
        if "columns" in rf and "rows" in rf:
            show_df(pd.DataFrame(rf["rows"], columns=rf["columns"]), "result_field (tabla)")
        elif "value" in rf:
            show_df(pd.DataFrame([rf]), "result_field (numérico)")
        elif "text" in rf:
            show_text("result_field (texto)", rf.get("text", ""))
        else:
            show_df(pd.DataFrame([rf]), "result_field")
    elif rf is not None:
        show_df(pd.DataFrame([{"value": rf}]), "result_field")

    if "justification" in data:
        show_text("justification", data.get("justification", ""))

    if "synonyms_found" in data:
        show_list("synonyms_found", data.get("synonyms_found"))

    # text_source (colapsable por chunk)
    ts = data.get("text_source") or []
    if isinstance(ts, list) and all(isinstance(x, dict) for x in ts) and ts:
        if display:
            display(HTML("<div style='margin:.6rem 0;font-weight:700;'>text_source</div>"))
        else:
            print("\n== text_source ==")

        for i, x in enumerate(ts, 1):
            pages = x.get("chunk_page")
            pages = ", ".join(map(str, pages)) if isinstance(pages, list) else str(pages)
            header = f"[{i}] {x.get('chunk_document','')} | {x.get('chunk_id','')} | page(s): {pages}"
            show_text(header, x.get("text", ""))
    elif "text_source" in data:
        show_text("text_source", ts)
