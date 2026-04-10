"""
Direct Proof: Auto-Policy Learning v1.0
Verification of Trust Threshold logic in LocalPermissionBroker
"""
import time
import os
from localagent.broker import LocalPermissionBroker

def proof_of_learning():
    print("🛠️ Initializing LocalPermissionBroker Proof (Auto-Learning)...")
    
    # Use a fresh test db
    db_path = "test_learning.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    broker = LocalPermissionBroker(db_path=db_path)
    
    intent = "append_to_file"
    resource = "temp/trusted_log.txt"

    print(f"\n--- Initial State ---")
    print(f"Policy: {intent} requires confirmation: {broker.policies[intent]['requires_confirmation']}")

    print(f"\n--- Step 1: Performing 8 successful approvals ---")
    for i in range(8):
        # Simulate approval cycle: Request -> Deny(Gated) -> Approve
        res = broker.request_permission({"intent": intent, "resource": resource, "context": {}})
        req_id = res["request_id"]
        
        # Approve it
        broker.confirm_permission(req_id, approved=True)
        print(f"✅ Approved Request {i+1}")

    print(f"\n--- Step 2: Verification (9th Request) ---")
    final_res = broker.request_permission({"intent": intent, "resource": resource, "context": {}})
    
    print(f"Granted: {final_res.get('granted')}")
    print(f"Policy requires confirmation: {broker.policies[intent]['requires_confirmation']}")
    
    if final_res.get("granted") and not broker.policies[intent]['requires_confirmation']:
        print("\n🏆 SUCCESS: Auto-policy update triggered successfully!")
        print("The broker correctly learned trust from historical approvals.")
    else:
        print("\n❌ FAILURE: Auto-policy logic did not trigger.")

    # Cleanup
    broker.conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    proof_of_learning()
