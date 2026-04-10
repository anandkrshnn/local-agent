"""
Proof of Life: Semantic Memory Engine Integration
"""
import json
from localagent.memory import MemoryEngine

def prove_memory():
    print("🧠 Initializing Semantic Memory Engine (DuckDB VSS)...")
    mem = MemoryEngine(db_path="demo_memory.duckdb")
    
    # 1. Store a memory
    test_tag = "Project Alpha-42 (Top Secret Archive)"
    print(f"📥 Storing memory: '{test_tag}'")
    mem.remember("secret_project", {"name": "Alpha-42", "status": "Archived"}, text_for_embedding=test_tag)
    
    # 2. Perform a semantic recall
    query = "What was that archived project?"
    print(f"🔍 Querying: '{query}'")
    results = mem.recall_similar(query, top_k=1)
    
    # 3. Display results
    print("\n--- RESULTS ---")
    if results and "error" not in results[0]:
        match = results[0]
        print(f"✅ Found Match! (Score: {match['score']:.4f})")
        print(f"📄 Event Type: {match['event_type']}")
        print(f"📦 Data: {json.dumps(match['payload'], indent=2)}")
    else:
        print(f"❌ Error during recall: {results}")
    
    mem.close()

if __name__ == "__main__":
    prove_memory()
