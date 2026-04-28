import time
import ollama  # <--- WAS MISSING
from qdrant_client import QdrantClient

# 1. Setup Connections
print("Connecting to Services...")

try:    
    # Using short service names works if they are in the same namespace
    client = QdrantClient(host="qdrant", port=6333)
    OLLAMA_HOST = "http://ollama:11434"
    
    # Check collections
    res = client.get_collections()
    print(f"✅ SUCCESS! Found collections: {res}")
except Exception as e:
    print(f"❌ CONNECTION FAILED: {e}")

def get_answer(question):
    try:
        print(f"DEBUG: Starting search for: {question}")
        hits = client.query(
            collection_name="tech_docs",
            query_text=question,
            limit=3
        )
        print(f"DEBUG: Found {len(hits)} hits from Qdrant.")

        # Updated to 'document' based on our previous fix
        context = " ".join([hit.metadata.get('document', '') for hit in hits])
        print("DEBUG: Context prepared. Sending to Ollama...")

        response = ollama.Client(host=OLLAMA_HOST).chat(
            model='llama3.2:1b',
            messages=[{'role': 'user', 'content': f"Context: {context}\n\nQuestion: {question}"}],
        )
        return response['message']['content']
    except Exception as e:
        print(f"DEBUG: Error in get_answer: {e}")
        return f"Error: {e}"

# Run the test
print("\n--- RAG TEST ---")
print(f"Answer: {get_answer('What is the status of our deployment?')}")

# Keep pod alive to read logs in Argo CD
while True:
    print("\n--- TRIGGERING RAG TEST ---", flush=True)
    ans = get_answer('What is the status of our deployment?')
    print(f"Answer: {ans}", flush=True)
    
    # This ensures the output hits the K8s logs immediately
    sys.stdout.flush() 
    
    print("Waiting 60s for next test...", flush=True)
    time.sleep(60)
