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
        # 2. Get facts from Qdrant
        # Note: Ensure the collection 'tech_docs' actually exists!
        hits = client.query(
            collection_name="tech_docs",
            query_text=question,
            limit=3
        )
        
        # Check if your metadata key is actually 'text'
        context = " ".join([hit.metadata.get('text', '') for hit in hits])

        # 3. Ask Ollama to explain those facts
        response = ollama.Client(host=OLLAMA_HOST).chat(
            model='llama3.2:1b',
            messages=[{'role': 'user', 'content': f"Context: {context}\n\nQuestion: {question}"}],
        )
        return response['message']['content']
    except Exception as e:
        return f"Error during RAG flow: {e}"

# Run the test
print("\n--- RAG TEST ---")
print(f"Answer: {get_answer('What is the status of our deployment?')}")

# Keep pod alive to read logs in Argo CD
while True:
    time.sleep(60)
