import os
from qdrant_client import QdrantClient

# Explicitly use the Service name and Port
# We hardcode the port here just to rule out the Env Var collision for now
client = QdrantClient(host="qdrant", port=6333)

print("Attempting to connect...")
try:
    client.get_collections()
    print("✅ Connected!")
except Exception as e:
    print(f"❌ Failed: {e}")
