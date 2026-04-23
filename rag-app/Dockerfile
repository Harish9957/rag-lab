# ---------- build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps for sentence-transformers (needs gcc for some wheels)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy app code + docs
COPY app.py .
COPY rag.py .
COPY rag_bedrock.py .
COPY docs/ docs/

# Non-root user
RUN groupadd -r rag && useradd -r -g rag -d /app rag && \
    chown -R rag:rag /app
USER rag

EXPOSE 8501

# Pre-download the embedding model at build time so startup is fast
RUN python -c "from langchain_community.embeddings import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})"

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/health')" || exit 1

ENTRYPOINT ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8501"]
