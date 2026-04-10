"""
Proof of Life: Expanded Tool Set Integration
"""
import json
import shutil
from pathlib import Path
from localagent.agent import LocalAgent
from localagent.config import Config

def prove_tools():
    print("🛠️ Initializing LocalAgent Tool Proof...")
    config = Config.default()
    
    # 1. Clean Sandbox
    if config.sandbox_root.exists():
        shutil.rmtree(config.sandbox_root)
    config.sandbox_root.mkdir(parents=True, exist_ok=True)
    
    agent = LocalAgent()
    
    print("\n--- TEST 1: append_to_file ---")
    # This should trigger 'requires_confirmation' in the LPB for write-ops in 'temp/*'
    args_append = {"path": "temp/test_notes.txt", "content": "Initial line from proof script."}
    print(f"📥 Executing tool: append_to_file with {args_append}")
    result1 = agent._execute_tool("append_to_file", args_append)
    
    if result1.get("requires_confirmation"):
        print("✅ Correct: LPB requested confirmation for append (WRITE).")
        print(f"🔑 Request ID: {result1['request_id']}")
        
        # Approve it manually
        print("👍 Approving action...")
        confirm_res = agent.broker.confirm_permission(result1['request_id'], approved=True)
        if confirm_res.get("granted"):
            # Execute again with pre-approved context (simulating the loop)
            args_append["pre_approved"] = True 
            # In real agent.chat, the loop handles this. Here we just call it with approval simulation.
            final_res = agent._execute_tool("append_to_file", args_append)
            print(f"✨ Result: {final_res}")
    else:
        print(f"❌ Error: Expected confirmation but got: {result1}")

    print("\n--- TEST 2: list_directory ---")
    # This should be GRANTED immediately as it's read-only
    print("🔍 Executing tool: list_directory")
    result2 = agent._execute_tool("list_directory", {"path": "."})
    print(f"📂 Sandbox Contents: {result2.get('result')}")
    
    if "test_notes.txt" in str(result2.get("result")):
        print("✅ Success: 'test_notes.txt' found in directory listing!")

    print("\n--- TEST 3: read_file ---")
    print("📖 Reading 'test_notes.txt'")
    result3 = agent._execute_tool("read_file", {"path": "test_notes.txt"})
    print(f"📝 Content: {result3.get('result')}")

    agent.close()

if __name__ == "__main__":
    prove_tools()
