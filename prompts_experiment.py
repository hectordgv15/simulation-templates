import sys
import yaml
from pathlib import Path
from prompts.prompts_engine import PromptOrchestrator

def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding = "utf-8"))

# Load configurations and prompts
base_global = "prompts/templates/global"
base_fields = "prompts/fields"
base_premises = "prompts/premises"

output_contract_file = "output_contract.yaml"
field_quant_file = "019_maturities.yaml"
field_qual_file = "063_cfo_ir.yaml"
question_17_file = "question_17.yaml"

extraction_output_contract = load_yaml(f"{base_global}/{output_contract_file}")["extraction_output_contract"]
audit_output_contract      = load_yaml(f"{base_global}/{output_contract_file}")["audit_output_contract"]
condition_output_contract  = load_yaml(f"{base_global}/{output_contract_file}")["condition_output_contract"]

field_quantitative_prompt = load_yaml(f"{base_fields}/{field_quant_file}")
field_qualitative_prompt  = load_yaml(f"{base_fields}/{field_qual_file}")
question_17               = load_yaml(f"{base_premises}/{question_17_file}")


# Quantitative Prompts
# -------------------------------------------------------------------------------------------------------------------
extract_quantitative_prompt = PromptOrchestrator.get_prompt(
    "quantitative/extract",
    **field_quantitative_prompt,
    output_contract        = extraction_output_contract,
    include_specifications = True,
    include_exclusions     = True,
    include_source_guides  = True,
    )

critique_quantitative_prompt = PromptOrchestrator.get_prompt(
    "quantitative/critique",
    **field_quantitative_prompt
    )

user_prompt = PromptOrchestrator.get_prompt(
    "global/user",
    user_type = "extract"
    )

# Qualitative Prompts
# -------------------------------------------------------------------------------------------------------------------
extract_qualitative_prompt = PromptOrchestrator.get_prompt(
    "qualitative/extract",
    **field_qualitative_prompt,
    output_contract       = extraction_output_contract,
    include_source_guides = True,
    )

critique_qualitative_prompt = PromptOrchestrator.get_prompt(
    "qualitative/critique",
    **field_qualitative_prompt,
    )

user_prompt = PromptOrchestrator.get_prompt(
    "global/user",
    user_type = "critique"
    )

# Evaluation Prompts
# -------------------------------------------------------------------------------------------------------------------
individual_conditions = PromptOrchestrator.get_prompt(
    "evaluation/conditions",
    premise_id         = "strategic_planning",
    regulatory_context = question_17["regulatory_context"],
    objective_premise  = question_17["premises"]["strategic_planning"]["description"],
    scoring_levels     = question_17["scoring_levels"],
    )

# User Prompt
user_prompt = PromptOrchestrator.get_prompt(
    "global/user",
    user_type = "evaluate"
    )

# Summary Prompt
summary_prompt = PromptOrchestrator.get_prompt(
    "global/summary",
    include_judgment = True,
    )

print(summary_prompt)