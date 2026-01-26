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
    "extract",
    **table_field, 
    template_type          = "quantitative", 
    output_language        = "es", 
    max_words              = None, 
    include_specifications = True, 
    include_exclusions     = True, 
    include_source_guides  = True,
    )

critique_quantitative = PromptOrchestrator.get_prompt(
    "critique",
    **table_field,
    template_type   = "quantitative",
    output_language = "es",
    max_words       = 150,
    )


# Qualitative Prompts
# -------------------------------------------------------------------------------------------------------------------
extract_qualitative = PromptOrchestrator.get_prompt(
    "extract",
    **macro_field,
    template_type          = "qualitative",
    output_language        = "es",
    max_words              = 500,
    include_source_guides  = True
    )


critique_qualitative = PromptOrchestrator.get_prompt(
    "critique",
    **macro_field,
    template_type   = "qualitative",
    output_language = "es",
    max_words       = 150,
    )



# Evaluation Prompt
evaluation_prompt = PromptOrchestrator.get_prompt(
    "evaluate",
    **evaluation_info,
    premise_id      = "strategic_planning",
    output_language = "es",
    )


# Summary Prompt
# -------------------------------------------------------------------------------------------------------------------
summary_prompt = PromptOrchestrator.get_prompt(
    "summarize",
    include_judgment = True,
    max_words        = 150,
    )