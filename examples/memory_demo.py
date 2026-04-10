"""
Memory Demo Example - Local Agent v0.1.0
Demonstrates the semantic memory engine (storing and recalling context).
"""

from localagent.agent import LocalAgent
from localagent.config import Config

def main():
    config = Config()
    agent = LocalAgent(config=config)
    
    # 1. Store a preference
    pref = "I prefer using dark mode for all my applications and I like the Inter font."
    print(f"Storing memory: '{pref}'")
    agent.store_memory(pref)
    
    # 2. Store another fact
    fact = "My project is named 'Local Agent' and its current version is 0.1.0."
    print(f"Storing memory: '{fact}'")
    agent.store_memory(fact)
    
    # 3. Recall using different wording (Semantic Search)
    query = "What are my UI settings?"
    print(f"\nRecalling for query: '{query}'")
    
    memories = agent.recall(query, limit=2)
    
    if memories:
        print("\nRetrieved Memories:")
        for i, m in enumerate(memories, 1):
            print(f"{i}. {m}")
    else:
        print("\nNo relevant memories found.")

if __name__ == "__main__":
    main()
