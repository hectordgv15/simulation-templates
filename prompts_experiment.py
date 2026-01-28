import sys
import yaml
from pathlib import Path
from prompts.prompts_engine import PromptOrchestrator

def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding = "utf-8"))

# Load configurations and prompts
base_fields = "prompts/fields"
base_premises = "prompts/premises"

# Field Definitions
table_field = load_yaml(Path(base_fields) /  "019_maturities.yaml")
macro_field = load_yaml(Path(base_fields) /  "063_cfo_ir.yaml")
evaluation_info = load_yaml(Path(base_premises) / "question_17.yaml")

# Quantitative fields
# -------------------------------------------------------------------------------------------------------------------
extract_quantitative = PromptOrchestrator.get_prompt(
    "extraction/extract",
    **table_field, 
    field_type          = "quantitative", 
    output_language        = "es", 
    max_characters         = None, 
    include_specifications = True, 
    include_exclusions     = True, 
    include_source_guides  = True,
    )

critique_quantitative = PromptOrchestrator.get_prompt(
    "extraction/critique",
    **table_field,
    field_type   = "quantitative",
    output_language = "es",
    max_characters  = 1000,
    )


# Qualitative Prompts
# -------------------------------------------------------------------------------------------------------------------
extract_qualitative = PromptOrchestrator.get_prompt(
    "extraction/extract",
    **macro_field,
    field_type          = "qualitative",
    output_language        = "es",
    max_characters         = 5000,
    include_source_guides  = True
    )


critique_qualitative = PromptOrchestrator.get_prompt(
    "extraction/critique",
    **macro_field,
    field_type   = "qualitative",
    output_language = "es",
    max_characters  = 1000,
    )


# Evaluation Prompt
# -------------------------------------------------------------------------------------------------------------------
evaluation_prompt = PromptOrchestrator.get_prompt(
    "evaluation/evaluate",
    **evaluation_info,
    premise_id      = "strategic_planning",
    output_language = "es",
    max_characters  = 1000,
    )


consolidate_prompt = PromptOrchestrator.get_prompt(
    "evaluation/consolidate",
    **evaluation_info,
    output_language = "es",
    max_characters  = 2000,
    )


# Summary Prompt
# -------------------------------------------------------------------------------------------------------------------
summary_prompt = PromptOrchestrator.get_prompt(
    "utils/summarize",
    include_judgment = True,
    max_characters   = 1000,
    )