import requests
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import os

# Instead of 'localhost', use the names we defined in the YAML env section
EMBED_URL = os.getenv("EMBED_URL", "http://localhost:8080/embed")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

def get_embedding(text):
    # This will now use 'http://embedding-api:80/embed' inside the cluster
    res = requests.post(EMBED_URL, json={"inputs": text})
    return res.json()[0]

# 1. Your 'Translator' (The pod you just tested)

def get_embedding(text):
    res = requests.post(EMBED_URL, json={"inputs": text})
    return res.json()[0]

# 2. Get vectors for two different sentences
vec_apple = get_embedding("I love eating red apples")
vec_fruit = get_embedding("My favorite snack is a piece of fruit")
vec_cargo = get_embedding("Argo CD is a GitOps tool")

# 3. Simple Logic: Are they similar?
# (In a real lab, you'd use Qdrant for this part)
print(f"Apple Vector (first 5): {vec_apple[:5]}")

# Connect to the Qdrant pod (via your 6333 port-forward)
client = QdrantClient(host="qdrant", port=6333)

# 1. Create the 'Library' (Only do this once)
client.recreate_collection(
    collection_name="lab_collection",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# 2. Add your Apple vector
client.upsert(
    collection_name="lab_collection",
    points=[
        {
            "id": 1,
            "vector": vec_apple, # The numbers you just saw!
            "payload": {"text": "I love eating red apples"}
        }
    ],
)

print("Stored in Qdrant successfully!")

# 1. Search for something related
query_text = "I need a crunchy fruit that grows on trees"
query_vector = get_embedding(query_text)

# 2. The New Search Syntax (2026 style)
results = client.query_points(
    collection_name="lab_collection",
    query=query_vector,
    limit=1
).points

# 3. Print the result
if results:
    print(f"\nSearch Query: {query_text}")
    print(f"AI Result: {results[0].payload['text']} (Score: {results[0].score:.4f})")


print(f"AI Result: {results[0].payload['text']} (Score: {results[0].score:.4f})")

# THE STABILITY LOOP: This keeps the container alive
print("Lab complete. Service is staying alive for inspection...")
import time
while True:
    time.sleep(60)
