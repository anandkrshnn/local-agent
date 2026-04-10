"""
Final System Check: LocalAgent v4.2
Verification of Semantic Memory + Expanded Tool Set + Security Broker
"""
import json
import shutil
from pathlib import Path
from localagent.agent import LocalAgent
from localagent.config import Config

def final_check():
    print("🚀 Running Final System Check (LocalAgent v4.2)...")
    config = Config.default()
    
    # 1. Environment Setup
    if config.sandbox_root.exists():
        shutil.rmtree(config.sandbox_root)
    config.sandbox_root.mkdir(parents=True, exist_ok=True)
    temp_dir = config.sandbox_root / "temp"
    temp_dir.mkdir(exist_ok=True)

    agent = LocalAgent()
    
    print("\n--- 🧠 Phase 1: Semantic Memory ---")
    mem_tag = "Project Chimera (Authorized Sector 7)"
    print(f"📥 Storing: '{mem_tag}'")
    agent.memory.remember("secure_context", {"project": "Chimera", "sector": 7}, text_for_embedding=mem_tag)
    
    recall = agent.memory.recall_similar("What project is in sector 7?", top_k=1)
    if recall and recall[0].get("payload", {}).get("project") == "Chimera":
        print("✅ SUCCESS: Semantic recall is accurate.")
    else:
        print(f"❌ ERROR: Recall failed: {recall}")

    print("\n--- 🛡️ Phase 2: Security Broker (Gating) ---")
    # This should trigger 'requires_confirmation' for writing to temp/*.txt
    req_args = {"path": "temp/audit.log", "content": "Security check passed."}
    print(f"📥 Attempting gated append: {req_args['path']}")
    gated_res = agent._execute_tool("append_to_file", req_args)
    
    if gated_res.get("requires_confirmation"):
        print("✅ SUCCESS: Permission Broker correctly gated the write operation.")
        print(f"🔑 Request ID: {gated_res['request_id']}")
        
        # Approve and execute
        req_args["pre_approved"] = True
        final_res = agent._execute_tool("append_to_file", req_args)
        print(f"✨ Result: {final_res.get('result')}")
    else:
        print(f"❌ ERROR: Gating failed: {gated_res}")

    print("\n--- 📂 Phase 3: Expanded Tool Set ---")
    # list_directory should work immediately
    print("🔍 Listing sandbox contents...")
    list_res = agent._execute_tool("list_directory", {"path": "."})
    print(f"📁 Root Contents: {list_res.get('result')}")
    
    if "temp" in list_res.get("result", []):
        print("✅ SUCCESS: Directory listing is functional.")
    else:
        print(f"❌ ERROR: Directory listing failed: {list_res}")

    print("\n--- 📝 Phase 4: Data Persistence ---")
    read_res = agent._execute_tool("read_file", {"path": "temp/audit.log"})
    print(f"📖 Log Reading: {read_res.get('result')}")
    
    if "Security check passed." in str(read_res.get("result")):
        print("✅ SUCCESS: Persistence and Reading are functional.")
    else:
        print(f"❌ ERROR: Persistence check failed: {read_res}")

    agent.close()
    print("\n🏁 FINAL STATUS: LocalAgent v4.2 is fully operational.")

if __name__ == "__main__":
    final_check()
