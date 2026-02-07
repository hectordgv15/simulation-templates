from __future__ import annotations

import yaml
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from prompts.prompts_engine import PromptOrchestrator

BASE_FIELDS = Path("prompts/fields")
BASE_QUESTIONS = Path("prompts/subfactors")


@lru_cache(maxsize = 256)
def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding = "utf-8"))


def _user_prompts(*user_types: str) -> Dict[str, str]:
    return {
        f"user_prompt_{t}": PromptOrchestrator.get_prompt("common/user", user_type = t)
        for t in user_types
    }


def _build_extraction_prompts(field_info: Mapping[str, Any]) -> Dict[str, Any]:
    field_type = field_info.get("field_type")
    
    if field_type not in {"quantitative", "qualitative"}:
        raise ValueError(f"field_type inválido: {field_type!r}")

    if field_type == "quantitative":
        base_extract = dict(
            output_language       = "es",
            max_characters        = 1000,
            include_normalization = True,
        )

        extract_quantitative = PromptOrchestrator.get_prompt(
            "extraction/extract",
            **field_info,
            **base_extract,
            include_source_guides  = True,
            include_synonyms       = True,
            include_specifications = True,
            include_exclusions     = True,
        )

        alternative_quantitative = PromptOrchestrator.get_prompt(
            "extraction/extract",
            **field_info,
            **base_extract,
            include_source_guides  = False,
            include_synonyms       = False,
            include_specifications = False,
            include_exclusions     = False,
        )

        critique_quantitative = PromptOrchestrator.get_prompt(
            "extraction/critique",
            **field_info,
            output_language        = "es",
            max_characters         = 1000,
            include_specifications = True,
            include_exclusions     = True,
        )

        return {
            "extract_quantitative"     : extract_quantitative,
            "alternative_quantitative" : alternative_quantitative,
            "critique_quantitative"    : critique_quantitative,
            **_user_prompts("extract", "critique"),
        }

    # qualitative
    extract_qualitative = PromptOrchestrator.get_prompt(
        "extraction/extract",
        **field_info,
        output_language             = "es",
        max_characters              = 5000,
        include_source_guides       = True,
        include_extraction_elements = True,
        include_traceability_rule   = True,
        include_coverage_rule       = True,
    )

    critique_qualitative = PromptOrchestrator.get_prompt(
        "extraction/critique",
        **field_info,
        output_language = "es",
        max_characters  = 1000,
    )

    summary_prompt = PromptOrchestrator.get_prompt(
        "extraction/summarize",
        include_judgment = True,
        max_characters   = 1000,
    )

    return {
        "extract_qualitative": extract_qualitative,
        "critique_qualitative": critique_qualitative,
        "summary_prompt": summary_prompt,
        **_user_prompts("extract", "critique", "summarize"),
    }


def _build_evaluation_prompts(evaluation_info: Mapping[str, Any]) -> Dict[str, Any]:
    premises = evaluation_info.get("premises") or {}
    if not isinstance(premises, dict):
        raise ValueError("evaluation_info['premises'] debe ser un dict")

    premises_evaluation_prompts = {
        premise_id: PromptOrchestrator.get_prompt(
            "evaluation/evaluate",
            **evaluation_info,
            premise_id      = premise_id,
            output_language = "es",
            max_characters  = 1000,
        )
        for premise_id in premises.keys()
    }

    consolidate_prompt = PromptOrchestrator.get_prompt(
        "evaluation/consolidate",
        **evaluation_info,
        output_language  = "es",
        max_characters   = 2000,
    )

    return {
        "premises_evaluation_prompts": premises_evaluation_prompts,
        "consolidate_prompt": consolidate_prompt,
        **_user_prompts("evaluate", "consolidate"),
    }

def load_prompts(
    process         : str = "extraction",
    *,
    field_name      : Optional[str] = None,
    question_name   : Optional[str] = None,
    field_info      : Optional[Mapping[str, Any]] = None,
    evaluation_info : Optional[Mapping[str, Any]] = None,
    base_fields     : Path = BASE_FIELDS,
    base_questions  : Path = BASE_QUESTIONS,
) -> Dict[str, Any]:
    """
    - process="extraction": field_name or field_info
    - process="evaluation": question_name or evaluation_info
    """
    if process == "extraction":
        if field_info is None:
            if not field_name:
                raise ValueError("For extraction, pass field_name or field_info")
            field_info = load_yaml(base_fields / f"{field_name}.yaml")
        return _build_extraction_prompts(field_info)

    if process == "evaluation":
        if evaluation_info is None:
            if not question_name:
                raise ValueError("For evaluation, pass question_name or evaluation_info")
            evaluation_info = load_yaml(base_questions / f"{question_name}.yaml")
        return _build_evaluation_prompts(evaluation_info)

    raise ValueError(f"Invalid process: {process!r}")