import os
import sys

# Ensure imports work from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService

def test_vector_db():
    print("=" * 60)
    print(" 🧠 ANALYZING PERSISTENT FAISS VECTOR DB")
    print("=" * 60)
    
    rag = RAGService()
    
    if not rag.vector_store:
        print("❌ Error: Vector DB is not initialized.")
        return
        
    docstore_dict = rag.vector_store.docstore._dict
    total_chunks = len(docstore_dict)
    print(f"\n✅ Vector database loaded successfully from disk!")
    print(f"✅ Total embedded document chunks: {total_chunks}")
    
    print("\n--- SAMPLE CHUNKS (Top 3) ---")
    
    # Grab the first 3 chunks to display
    chunks = list(docstore_dict.values())[:3]
    for i, chunk in enumerate(chunks):
        print(f"\n[Chunk {i+1}]")
        print(chunk.page_content.strip())
        print("-" * 40)

if __name__ == "__main__":
    test_vector_db()
