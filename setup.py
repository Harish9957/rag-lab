from qdrant_client import QdrantClient

# Connect to your port-forwarded instance
client = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "tech_docs"

try:
    # 1. Clean up the old incompatible collection
    print(f"Deleting old {COLLECTION_NAME}...")
    client.delete_collection(collection_name=COLLECTION_NAME)
except Exception:
    pass

# 2. Use the 'add' method to create AND seed simultaneously
# This automatically handles the vector math for you
print("Creating and seeding collection with FastEmbed...")
client.add(
    collection_name=COLLECTION_NAME,
    documents=[
        "ArgoCD is our GitOps tool located in the argocd namespace.",
        "The Ollama service provides the Llama 3.2:1b model for inference.",
        "The ingress-nginx controller is running with a LoadBalancer service."
    ],
    ids=[1, 2, 3]
)

print("✅ SUCCESS: Qdrant is seeded with facts!")
