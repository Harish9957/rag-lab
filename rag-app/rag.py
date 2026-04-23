"""
RAG Pipeline — Load runbooks into ChromaDB + Query via Ollama
Usage:
  python rag.py load          # Load docs into ChromaDB (one-time)
  python rag.py query "Why is metadata-grpc OOMKilled?"
"""

import sys
import os
import chromadb
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
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

    # Load all .md files
    loader = DirectoryLoader(DOCS_DIR, glob="**/*.md", loader_cls=TextLoader)
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s)")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n---\n", "\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    # Get or create collection
    collection = chroma.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    # Embed and store
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
    """Query ChromaDB for relevant context, then ask Ollama."""
    print(f"\nQuestion: {question}\n")

    # Retrieve relevant chunks from ChromaDB
    collection = chroma.get_collection(name=COLLECTION)
    query_embedding = embeddings.embed_query(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
    )

    context = "\n\n".join(results["documents"][0])
    print(f"--- Retrieved {len(results['documents'][0])} relevant chunks ---\n")

    # Build prompt
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are an on-call SRE assistant. Use the following runbook context to answer the question.
If the context doesn't contain enough info, say so — don't make things up.

Context:
{context}

Question: {question}

Answer:""",
    )

    # Call Ollama
    llm = ChatOllama(
        model="llama3.2:3b",
        base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
        temperature=0,
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
        print('  python rag.py load')
        print('  python rag.py query "your question"')
        sys.exit(1)

    command = sys.argv[1]

    if command == "load":
        load_docs()
    elif command == "query":
        if len(sys.argv) < 3:
            print('Usage: python rag.py query "your question"')
            sys.exit(1)
        query(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
