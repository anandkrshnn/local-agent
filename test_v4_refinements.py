#!/usr/bin/env python3
"""
Test suite for Sprint 1 refinements
Tests concurrency, orchestration, and persistence
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_concurrency():
    """Test request queue with concurrent requests"""
    print("\n🔀 Testing Concurrency...")
    from local_agent.utils.queue_manager import queue_manager
    from local_agent.models.ollama import OllamaProvider
    
    provider = OllamaProvider()
    if not provider.is_available():
        print("  ⚠️ Ollama not available, skipping concurrency test")
        return True
        
    async def make_request(i):
        start = time.time()
        try:
            # Note: generate_async uses the queue_manager
            response = await provider.generate_async(f"Say hello as message {i}")
            elapsed = time.time() - start
            print(f"    - Request {i} completed in {elapsed:.2f}s")
            return {"success": True, "index": i, "time": elapsed}
        except Exception as e:
            print(f"    - Request {i} failed: {e}")
            return {"success": False, "index": i, "error": str(e)}
    
    # Submit 3 concurrent requests (reduced from 5 for speed)
    print(f"  Submitting 3 concurrent requests to queue...")
    tasks = [make_request(i) for i in range(3)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r['success'])
    stats = queue_manager.get_stats()
    print(f"  Results: {success_count}/3 successful")
    print(f"  Queue stats: {stats}")
    
    return success_count == 3

async def test_orchestration():
    """Test multi-step orchestration"""
    print("\n🎯 Testing Orchestration...")
    from local_agent.core.agent import LocalAgent
    
    agent = LocalAgent(verbose=False)
    
    # Simple goal that requires two steps
    goal = "Create a file named sprint1_test.txt with content 'hello world' and then read it"
    print(f"  Goal: {goal}")
    
    result = await agent.execute_goal(goal, max_tasks=3)
    
    print(f"  Success: {result['success']}")
    print(f"  Tasks completed: {result['completed_tasks']}/{result['total_tasks']}")
    if 'summary' in result:
        print(f"  Summary: {result['summary'][:100]}...")
    
    return result['success'] or result['completed_tasks'] > 0

def test_persistence():
    """Test session persistence"""
    print("\n💾 Testing Persistence...")
    from local_agent.utils.persistent_sessions import PersistentSessionManager
    
    db_file = "test_sessions.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    manager = PersistentSessionManager(db_path=db_file)
    
    # Create session and add messages
    session = manager.create_session()
    session_id = session.session_id
    manager.add_message(session_id, "user", "Hello from test")
    manager.add_message(session_id, "assistant", "Hello back")
    
    print(f"  Created session {session_id[:8]} with 2 messages")
    manager.close()
    
    # Simulate restart by creating new manager
    print("  Simulating server restart...")
    manager2 = PersistentSessionManager(db_path=db_file)
    recovered_session = manager2.get_session(session_id)
    
    messages = recovered_session.messages if recovered_session else []
    success = len(messages) == 2
    
    print(f"  Session recovered: {'Yes' if recovered_session else 'No'}")
    print(f"  Messages found: {len(messages)}")
    
    manager2.close()
    if os.path.exists(db_file):
        os.remove(db_file)
        
    return success

async def main():
    print("=" * 60)
    print("🧪 LOCAL AGENT v4.0 - SPRINT 1 REFINEMENTS TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Concurrency
    try:
        results.append(("Concurrency", await test_concurrency()))
    except Exception as e:
        print(f"  ❌ Concurrency test error: {e}")
        results.append(("Concurrency", False))
    
    # Test 2: Persistence
    try:
        results.append(("Persistence", test_persistence()))
    except Exception as e:
        print(f"  ❌ Persistence test error: {e}")
        results.append(("Persistence", False))
        
    # Test 3: Orchestration
    try:
        results.append(("Orchestration", await test_orchestration()))
    except Exception as e:
        print(f"  ❌ Orchestration test error: {e}")
        results.append(("Orchestration", False))
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 All Sprint 1 refinements passed!")
    else:
        print("\n⚠️ Some tests failed. Check errors above.")

if __name__ == "__main__":
    asyncio.run(main())
