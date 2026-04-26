import os
import time
import requests
from qdrant_client import QdrantClient

# Get variables from your app.yaml
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT_NUM", 6333))

def connect_with_retry(retries=5, delay=5):
    print(f"Attempting to connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    for i in range(retries):
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            # Check if it's actually alive
            client.get_collections()
            print("Successfully connected to Qdrant!")
            return client
        except Exception as e:
            print(f"Connection failed (Attempt {i+1}/{retries}). Retrying in {delay}s...")
            time.sleep(delay)
    raise Exception("Could not connect to Qdrant after multiple retries.")

if __name__ == "__main__":
    # 1. Wait for DB
    client = connect_with_retry()
    
    # 2. Rest of your logic here...
    print("Running RAG logic...")
    
    # 3. Keep alive for inspection
    while True:
        time.sleep(60)
