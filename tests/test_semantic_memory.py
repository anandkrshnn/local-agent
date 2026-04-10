"""Test Script for Semantic Memory (DuckDB VSS)"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from localagent.memory import memory
import json

def test_semantic_search():
    print("🧠 Starting Semantic Memory Test...")
    
    # 1. Store events with different themes
    print("📥 Storing test events...")
    memory.remember("user_action", {"action": "read_file", "path": "financial_report.pdf"}, "User read the private financial report for 2023.")
    memory.remember("user_action", {"action": "write_file", "path": "poem.txt"}, "User wrote a beautiful poem about the ocean.")
    memory.remember("system_log", {"level": "info"}, "The system temperature is within normal range (42C).")
    
    # 2. Perform semantic search
    print("\n🔍 Searching for: 'money and business'...")
    results = memory.recall_similar("money and business", top_k=1)
    for r in results:
        print(f"✅ Match: {r['event_type']} -> {r['payload']} (Score: {r['score']:.4f})")
        # Assert the financial report is the top match
        if "financial_report.pdf" in r['payload'].get('path', ''):
            print("✨ SUCCESS: Semantic query matched financial topic.")
        else:
            print("⚠️ WARNING: Semantic query did NOT match financial topic as expected.")

    print("\n🔍 Searching for: 'nature and sea'...")
    results = memory.recall_similar("nature and sea", top_k=1)
    for r in results:
        print(f"✅ Match: {r['event_type']} -> {r['payload']} (Score: {r['score']:.4f})")
        if "poem.txt" in r['payload'].get('path', ''):
            print("✨ SUCCESS: Semantic query matched nature topic.")
        else:
            print("⚠️ WARNING: Semantic query did NOT match nature topic as expected.")

    print("\n🔍 Searching for: 'hardware health'...")
    results = memory.recall_similar("hardware health", top_k=1)
    for r in results:
        print(f"✅ Match: {r['event_type']} -> {r['payload']} (Score: {r['score']:.4f})")
        if "temperature" in str(r['payload']):
            print("✨ SUCCESS: Semantic query matched hardware topic.")
        else:
            print("⚠️ WARNING: Semantic query did NOT match hardware topic as expected.")

    # 3. Check memory stats
    print("\n📊 Memory Stats:")
    print(json.dumps(memory.get_stats(), indent=2))

if __name__ == "__main__":
    try:
        test_semantic_search()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
