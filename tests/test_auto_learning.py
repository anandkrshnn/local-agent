# tests/test_auto_learning.py
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from localagent.agent import LocalAgent

def test_auto_learning():
    agent = LocalAgent()
    print("🧪 Testing Auto-Policy Learning...\n")

    path = "temp/auto_test_notes.txt"
    intent = "append_to_file"

    print("Step 1: Performing 8 approved operations to reach trust threshold...")
    for i in range(8):
        print(f"\n[Attempt {i+1}] Requesting append...")
        result = agent.chat(f"Append 'Line {i+1}' to {path}")
        
        if "⚠️ Action requires confirmation" in result:
            request_id = result.split("Request ID: ")[1].strip()
            print(f"🔑 Gated! ID: {request_id}. Automatically approving...")
            agent.broker.confirm_permission(request_id, approved=True)
            print("✅ Approved.")
        else:
            print(f"✨ Result: {result}")

    print("\n--- TRUST THRESHOLD REACHED ---")

    print("\nStep 2: Performing 9th operation (Should be automatic)...")
    result_9 = agent.chat(f"Append 'Line 9 (Automatic)' to {path}")
    print(f"Result 9: {result_9}")

    if "⚠️" not in result_9:
        print("\n🏆 SUCCESS: Auto-policy learning worked! Confirmation disabled for this pattern.")
    else:
        print("\n❌ FAILURE: Confirmation was still required.")

    print("\n✅ Auto-policy learning test sequence completed.")

if __name__ == "__main__":
    test_auto_learning()
