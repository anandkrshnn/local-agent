# verify_memory.py
from localagent.memory import MemoryEngine
import json
import os

def test_semantic_memory():
    print("🧠 Testing Semantic Memory with DuckDB VSS...\n")
    
    db_file = "agent_test_memory.duckdb"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    memory = MemoryEngine(db_path=db_file)
    
    # Store some varied events
    memory.remember("file_action", {"action": "read", "path": "financial_report.pdf", "content": "Q3 revenue up 23%"})
    memory.remember("file_action", {"action": "read", "path": "poem.txt", "content": "The sea whispers secrets to the shore"})
    memory.remember("system_log", {"temperature": 72, "status": "normal", "component": "cpu"})
    
    print("Stored 3 test events.\n")
    
    # Semantic searches
    tests = [
        "money and business performance",
        "nature and ocean poem",
        "hardware temperature and cpu health"
    ]
    
    for query in tests:
        print(f"Query: '{query}'")
        results = memory.recall_similar(query, top_k=1)
        if results and "payload" in results[0]:
            print(f"   → Best match: {results[0]['payload']}")
            print(f"   → Score: {results[0].get('score', 'N/A'):.4f}\n")
        else:
            print(f"   → Result: {results}\n")
    
    print("✅ Semantic Memory test completed.")
    print(f"Stats: {memory.get_stats()}")

if __name__ == "__main__":
    test_semantic_memory()
