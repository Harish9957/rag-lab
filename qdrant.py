import time
from qdrant_client import QdrantClient

# HARDCODE FOR THE FINAL TEST
# This proves the connection is possible
print("Connecting to Qdrant at 'qdrant:6333'...")

try:
    # We use the Service name directly here
    client = QdrantClient(host="qdrant", port=6333)
    
    # Check collections
    res = client.get_collections()
    print(f"✅ SUCCESS! Found collections: {res}")
except Exception as e:
    print(f"❌ STILL FAILING: {e}")

# Keep pod alive so we can read this win!
while True:
    time.sleep(60)
