import ollama
from qdrant_client import QdrantClient

# 1. Connect to your K8s services
qdrant = QdrantClient(host="qdrant.default.svc.cluster.local", port=6333)
OLLAMA_URL = "http://ollama.default.svc.cluster.local:11434"

def rag_chat(user_query):
    # 2. Retrieve: Search Qdrant for relevant technical docs
    search_result = qdrant.query(
        collection_name="tech_docs",
        query_text=user_query,
        limit=3
    )
    context = "\n".join([r.document for r in search_result])

    # 3. Augment: Create the prompt with the "Context"
    prompt = f"Using this context: {context}\n\nQuestion: {user_query}"

    # 4. Generate: Send to Ollama
    response = ollama.Client(host=OLLAMA_URL).generate(
        model="llama3.2:1b", 
        prompt=prompt
    )
    return response['response']

print(rag_chat("How is our ArgoCD configured?"))
