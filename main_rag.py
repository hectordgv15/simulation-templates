# .\myenv\Scripts\activate
import os
import time
import yaml
import json
from pathlib import Path
from jinja2 import Template

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



def chunk_line(doc, i=None):
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


def retrieval_with_answer():
    """
    Retrieve the most relevant documents and response
    """
    # OpenAI embeddings (reemplazo de BedrockEmbeddings)
    embeddings = OpenAIEmbeddings(
        model  = "text-embedding-3-small"
    )

    vector_store = FAISS.load_local(
        "vector_index",  # load folder FAISS
        embeddings,      # embeddings
        allow_dangerous_deserialization = True
    )
    
    # Load configurations and prompts
    output_contract = load_yaml("prompts/templates/global/output_contract.yaml")["extraction_output_contract"]
    field_quantitative_prompt = load_yaml("prompts/fields/019_maturities.yaml")

    retrieved_docs = vector_store.similarity_search(field_quantitative_prompt["retrieval_keywords"], k = 15)
    
    chunks = "\n".join(chunk_line(doc, i) for i, doc in enumerate(retrieved_docs))

    print(chunks)

    extract_quantitative_prompt = PromptOrchestrator.get_prompt(
        "quantitative/quantitative_extract",
        **field_quantitative_prompt,
        output_contract = output_contract,
        include_specifications    = False,
        include_exclusions        = False,
        include_source_guides     = True,
        )

    user_prompt = PromptOrchestrator.get_prompt(
        "global/user",
        user_type = "extract",
        chunks = chunks,
        )

    model = init_chat_model(
        model       = "gpt-5.2", # "gpt-4.1-mini"
        temperature = 0.0,
        top_p       = 1.0,
        max_tokens  = 3000
        )

    messages = [
        {"role": "system", "content": extract_quantitative_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    response = model.invoke(messages)

    return response


if __name__ == "__main__":
    start_time = time.time()
    answer = retrieval_with_answer()
    end_time = time.time()
    print("\n\n=== Response ===\n")
    print(answer.content)
    print(f"\n\n[Elapsed time: {end_time - start_time:.2f} seconds]")