from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(host="qdrant", port=6333)

# 1. Create the Collection (Use size 384 for standard small embeddings)
client.create_collection(
    collection_name="tech_docs",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# 2. Add some "Facts" about your cluster
points = [
    PointStruct(
        id=1,
        vector=[0.1] * 384, # Replace with real embeddings in production
        payload={
            "text": "ArgoCD is configured to sync automatically every 3 minutes for the 'production' project."
        }
    ),
    PointStruct(
        id=2,
        vector=[0.2] * 384,
        payload={
            "text": "The ingress-nginx controller is using a LoadBalancer service with an external IP of 1.2.3.4."
        }
    )
]

client.add(
    collection_name="tech_docs",
    documents=[
        "ArgoCD is configured to sync automatically every 3 minutes.",
        "The ingress-nginx controller handles external traffic."
    ]
)
print("✅ tech_docs collection created and seeded!")
