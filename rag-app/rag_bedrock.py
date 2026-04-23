"""
RAG Pipeline (Bedrock Edition) — Load runbooks into ChromaDB + Query via AWS Bedrock Claude
Usage:
  python rag_bedrock.py load          # Load docs into ChromaDB (one-time)
  python rag_bedrock.py query "Why is metadata-grpc OOMKilled?"
"""

import sys
import os
import chromadb
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "anthropic.claude-3-5-haiku-20241022-v1:0")
BEDROCK_REGION = os.getenv("AWS_REGION", "us-west-2")
COLLECTION = "runbooks"
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

# ---------------------------------------------------------------------------
# Embeddings (runs locally, small model ~80MB)
# ---------------------------------------------------------------------------
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

# ---------------------------------------------------------------------------
# ChromaDB client
# ---------------------------------------------------------------------------
chroma = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)


def load_docs():
    """Load markdown docs from docs/ folder, chunk them, embed, store in ChromaDB."""
    print(f"Loading docs from {DOCS_DIR}...")

    loader = DirectoryLoader(DOCS_DIR, glob="**/*.md", loader_cls=TextLoader)
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n---\n", "\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    collection = chroma.get_or_create_collection(
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

    print(f"Stored {len(chunks)} chunks in ChromaDB collection '{COLLECTION}'")


def query(question: str):
    """Query ChromaDB for relevant context, then ask Bedrock Claude."""
    print(f"\nQuestion: {question}\n")

    collection = chroma.get_collection(name=COLLECTION)
    query_embedding = embeddings.embed_query(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
    )

    context = "\n\n".join(results["documents"][0])
    print(f"--- Retrieved {len(results['documents'][0])} relevant chunks ---\n")

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are an on-call SRE assistant. Use the following runbook context to answer the question.
If the context doesn't contain enough info, say so — don't make things up.

Context:
{context}

Question: {question}

Answer:""",
    )

    llm = ChatBedrock(
        model_id=BEDROCK_MODEL,
        region_name=BEDROCK_REGION,
        model_kwargs={"temperature": 0, "max_tokens": 1024},
    )

    formatted = prompt.format(context=context, question=question)
    response = llm.invoke(formatted)

    print(response.content)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python rag_bedrock.py load')
        print('  python rag_bedrock.py query "your question"')
        sys.exit(1)

    command = sys.argv[1]

    if command == "load":
        load_docs()
    elif command == "query":
        if len(sys.argv) < 3:
            print('Usage: python rag_bedrock.py query "your question"')
            sys.exit(1)
        query(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
