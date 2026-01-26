# .\myenv\Scripts\activate
import os
import time
import yaml
import json
from pathlib import Path
from jinja2 import Template
import json

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate

import sys
from prompts.prompts_engine import PromptOrchestrator

from dotenv import load_dotenv
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding = "utf-8"))


def chunk_line(doc, i = None):
    """
    Format a document chunk into a single line with metadata
    """
    md = doc.metadata or {}

    text = (doc.page_content or "").replace("\n", " ").strip()

    chunk_document = md.get("chunk_document") or md.get("source") or "unknown"
    chunk_document = os.path.basename(chunk_document)  # opcional: solo nombre

    chunk_page = md.get("chunk_page")
    if chunk_page is None:
        chunk_page = md.get("page_label", md.get("page", "unknown"))

    chunk_id = md.get("chunk_id") or getattr(doc, "id", None)
    if not chunk_id:
        p = md.get("page", md.get("page_label", "unk"))
        chunk_id = f"{chunk_document}::p{p}::c{i if i is not None else 0}"

    return f"text: {text} | chunk_id: {chunk_id} | chunk_page: {chunk_page} | chunk_document: {chunk_document}"


def retrieval_with_answer(field_info     = None,
                          field_type     = None,
                          user_prompt    = None,
                          extract_prompt = None,
                          k_docs         = 15
                          ):
    """
    Retrieve the most relevant documents and response
    """
    # OpenAI embeddings (reemplazo de BedrockEmbeddings)
    embeddings = OpenAIEmbeddings(
        model  = "text-embedding-3-small"
    )
    
    # Extract prompt
    extract_prompt = PromptOrchestrator.get_prompt(
        "extract",
        **field_info,
        template_type          = field_type,
        output_language        = "es",
        max_words              = 500,
        include_source_guides  = True
        )

    # Load FAISS vector store
    vector_store = FAISS.load_local(
        "vector_index",  # load folder FAISS
        embeddings,      # embeddings
        allow_dangerous_deserialization = True
    )

    # Similarity search
    retrieved_docs = vector_store.similarity_search(field_info["retrieval_keywords"], k = k_docs)
    
    # Prepare chunks
    chunks = "\n".join(chunk_line(doc, i) for i, doc in enumerate(retrieved_docs))
    
    # User prompt for extraction
    user_prompt = PromptOrchestrator.get_prompt(
        "user",
        user_type = "extract",
        chunks = chunks
        )

    # Initialize model
    model = init_chat_model(
        model       = "gpt-5.2",
        temperature = 0.0,
        top_p       = 1.0,
        max_tokens  = 3000
        )
    
    # Create messages
    messages = [
        {"role": "system", "content": extract_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    response = model.invoke(messages)

    return response, extract_prompt


def summarize_content(content = None):
    """
    Summarize the content provided
    """
    # Summary prompt
    summary_prompt = PromptOrchestrator.get_prompt(
        "summarize",
        include_judgment = True,
        max_words        = 150,
        )
        
    # User prompt for summary
    user_prompt = PromptOrchestrator.get_prompt(
        "user",
        user_type = "summarize",
        content = content
        )

    # Initialize model
    model = init_chat_model(
        model       = "gpt-5.2",
        temperature = 0.0,
        top_p       = 1.0,
        max_tokens  = 3000
        )

    # Create messages
    messages = [
        {"role": "system", "content": summary_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    response = model.invoke(messages)

    return response, summary_prompt



if __name__ == "__main__":
    # Load configurations and prompts
    variables_list = ["063_cfo_ir", "064_marketing_strategy", "065_product_launch"]
    
    base_fields = "prompts/fields"
    macro_info = load_yaml(Path(base_fields) /  f"{variables_list[0]}.yaml")

    # Raw retrieval and answer
    answer = retrieval_with_answer(
        field_info     = macro_info,
        field_type     = "qualitative",
        k_docs         = 15
        )
    
    normalized_answer = json.loads(answer[0].content)

    # Summary
    summary = summarize_content(
        content = normalized_answer["value"]["value"]
        )
    
    # Extract multiple variables and summarize
    values_list = []

    extracted_by_variable = []

    for var_name in variables_list:
        field_info = load_yaml(Path(base_fields) / f"{var_name}.yaml")

        response, _ = retrieval_with_answer(
            field_info = field_info,
            field_type = "qualitative",
            k_docs     = 15
        )

        normalized_answer = json.loads(response.content)
        value_text = normalized_answer.get("value", {}).get("value", "")

        values_list.append(value_text)
        extracted_by_variable.append({"variable": var_name, "value": value_text})

    # Give a summary of all extracted values
    content_for_summary = "\n\n".join(
        f"### {item['variable']}\n{item['value']}"
        for item in extracted_by_variable
    )

    summary, _ = summarize_content(content = content_for_summary)
    print(summary.content)