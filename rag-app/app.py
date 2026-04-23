"""
RAG API Server — FastAPI wrapper for the RAG pipeline.
Endpoints:
  POST /load        — Load docs into ChromaDB
  POST /query       — Query the RAG pipeline
  GET  /health      — Health check
  GET  /ready       — Readiness check (ChromaDB reachable)
"""

import os
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
LLM_BACKEND = os.getenv("LLM_BACKEND", "bedrock")  # "bedrock" or "ollama"
COLLECTION = "runbooks"
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

# ---------------------------------------------------------------------------
# ChromaDB client
# ---------------------------------------------------------------------------
_chroma = None


def get_chroma():
    global _chroma
    if _chroma is None:
        _chroma = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
    return _chroma


# ---------------------------------------------------------------------------
# LLM (lazy init)
# ---------------------------------------------------------------------------
_llm = None


def get_llm():
    global _llm
    if _llm is not None:
        return _llm

    if LLM_BACKEND == "bedrock":
        from langchain_aws import ChatBedrock
        _llm = ChatBedrock(
            model_id=os.getenv("BEDROCK_MODEL", "anthropic.claude-3-5-haiku-20241022-v1:0"),
            region_name=os.getenv("AWS_REGION", "us-west-2"),
        )
    else:
        from langchain_ollama import ChatOllama
        _llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            base_url=f"http://{os.getenv('OLLAMA_HOST', 'localhost')}:{os.getenv('OLLAMA_PORT', '11434')}",
        )
    return _llm


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an on-call SRE assistant. Use the following runbook context to answer the question.
If the context doesn't contain enough info, say so — don't make things up.

Context:
{context}

Question: {question}

Answer:""",
)

# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(title="RAG Runbook Assistant", version="1.0.0")


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    chunks_used: int


class LoadResponse(BaseModel):
    documents_loaded: int
    chunks_stored: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        get_chroma().heartbeat()
        return {"status": "ready", "chromadb": "reachable"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ChromaDB unreachable: {e}")


@app.post("/load", response_model=LoadResponse)
def load_docs():
    loader = DirectoryLoader(DOCS_DIR, glob="**/*.md", loader_cls=TextLoader)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n---\n", "\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)

    collection = get_chroma().get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    for i, chunk in enumerate(chunks):
        embedding = embeddings.embed_query(chunk.page_content)
        collection.add(
            ids=[f"chunk_{i}"],
            embeddings=[embedding],
            documents=[chunk.page_content],
            metadatas=[{"source": chunk.metadata.get("source", "unknown")}],
        )

    return LoadResponse(documents_loaded=len(documents), chunks_stored=len(chunks))


@app.post("/query", response_model=QueryResponse)
def query_rag(req: QueryRequest):
    try:
        collection = get_chroma().get_collection(name=COLLECTION)
    except Exception:
        raise HTTPException(status_code=400, detail="Collection not found. POST /load first.")

    query_embedding = embeddings.embed_query(req.question)
    results = collection.query(query_embeddings=[query_embedding], n_results=3)

    context = "\n\n".join(results["documents"][0])
    sources = list({m.get("source", "unknown") for m in results["metadatas"][0]})

    llm = get_llm()
    formatted = PROMPT.format(context=context, question=req.question)
    response = llm.invoke(formatted)

    return QueryResponse(
        question=req.question,
        answer=response.content,
        sources=sources,
        chunks_used=len(results["documents"][0]),
    )
