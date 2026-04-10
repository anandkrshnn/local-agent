"""
Test Script for LocalAgent Semantic Recall (Zero-Context Test)
"""
import sys
import os
from pathlib import Path
import time

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from localagent.agent import LocalAgent
from localagent.memory import MemoryEngine
from localagent.broker import LocalPermissionBroker

def test_agent_recall():
    print("🤖 Starting Agent Recall Test...")
    
    # Use unique test DBs
    test_mem = "recall_test_v5.duckdb"
    test_audit = "recall_test_v5.db"
    
    # Cleanup previous run if possible
    for f in [test_mem, test_audit]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    # Initialize agent
    agent = LocalAgent(model="phi3:mini")
    agent.max_iterations = 1  # Speed up for demonstration
    agent.memory = MemoryEngine(db_path=test_mem)
    agent.broker = LocalPermissionBroker(db_path=test_audit)
    
    # 1. Provide a specific piece of information
    print("\n👤 > My secret tag is 'Project Alpha-42'.")
    agent.chat("My secret tag is 'Project Alpha-42'.")
    
    # IMPORTANT: Close and reopen to simulate full session reset and release file locks
    agent.close()
    print("\n[Simulating New Session - Clearing context and releasing file locks...]")
    time.sleep(1)
    
    # Re-initialize
    agent = LocalAgent(model="phi3:mini")
    agent.memory = MemoryEngine(db_path=test_mem)
    agent.broker = LocalPermissionBroker(db_path=test_audit)
    
    # 2. Ask about the information
    print("\n👤 > What was the name of that project tag I mentioned earlier?")
    response = agent.chat("What was the name of that project tag I mentioned earlier?")
    print(f"🤖 {response}")
    
    # 3. Verification
    if "Alpha-42" in response:
        print("\n✨ SUCCESS: Agent recalled 'Alpha-42' from semantic memory!")
    else:
        print("\n❌ FAILURE: Agent did not recall the tag. Result was:")
        print(response)
    
    agent.close()

if __name__ == "__main__":
    test_agent_recall()
