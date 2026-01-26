import os
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def ingestion_workflow_pdf(doc_urls, index_dir = "vector_index"):
    """
    Load one or multiple PDFs, split into chunks preserving metadata (source & page),
    create embeddings and store/update FAISS vector index.
    """
    start = time.time()

    # 0) Normalize input: str -> [str]
    if isinstance(doc_urls, str):
        doc_urls = [doc_urls]

    # 1) Text splitter (same as before)
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        separators    = ["\n\n", "\n", ". ", " ", ""],
        chunk_size    = 1000,
        chunk_overlap = 120,
    )

    # 2) Embeddings (initialize once)
    embeddings = OpenAIEmbeddings(model = "text-embedding-3-small")

    # 3) Load or create the vector store (initialize once)
    if os.path.exists(index_dir):
        vector_store = FAISS.load_local(
            index_dir,
            embeddings,
            allow_dangerous_deserialization = True
            )
    else:
        vector_store = None

    total_chunks = 0

    # 4) Iterate through documents
    for doc_url in doc_urls:
        loader = PyPDFLoader(doc_url)
        docs_loader = loader.load()

        docs_chunks = splitter.split_documents(docs_loader)

        print(f"[{os.path.basename(doc_url)}] Split into {len(docs_chunks)} sub-documents.")
        total_chunks += len(docs_chunks)

        # 5) Add documents to existing store or create a new one
        if vector_store is None:
            vector_store = FAISS.from_documents(docs_chunks, embeddings)
        else:
            vector_store.add_documents(docs_chunks)

    # 6) Save once at the end
    if vector_store is not None:
        vector_store.save_local(index_dir)

    end = time.time()
    print(f"Total chunks: {total_chunks} | Time: {end - start:.2f}s")
    return vector_store


if __name__ == "__main__":
    docs = [
        "annual_reports/cuentas-anuales-consolidadas.pdf",
    ]

    ingestion_workflow_pdf(docs)
