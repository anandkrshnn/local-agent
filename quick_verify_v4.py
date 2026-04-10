#!/usr/bin/env python3
"""Quick verification for Local Agent v4.0"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 50)
    print("🔍 LOCAL AGENT v4.0 - QUICK VERIFICATION")
    print("=" * 50)
    
    results = []
    
    # 1. Core imports
    print("\n📦 Testing imports...")
    try:
        from local_agent.core.agent import LocalAgent
        from local_agent.models.router import ModelRouter
        from local_agent.tools.registry import ToolRegistry
        from local_agent.utils.sessions import SessionManager
        results.append(("Core imports", True))
        print("  ✅ All core modules imported")
    except ImportError as e:
        results.append(("Core imports", False))
        print(f"  ❌ Import failed: {e}")
        return
    
    # 2. Agent initialization
    print("\n🤖 Testing agent initialization...")
    try:
        agent = LocalAgent(verbose=False)
        results.append(("Agent init", True))
        print("  ✅ Agent created successfully")
    except Exception as e:
        results.append(("Agent init", False))
        print(f"  ❌ Agent init failed: {e}")
    
    # 3. Model Router
    print("\n🎯 Testing Model Router...")
    try:
        router = ModelRouter()
        status = router.get_status()
        providers = [p['name'] for p in status['providers'] if p['available']]
        results.append(("Model Router", True))
        print(f"  ✅ Router initialized. Available: {providers if providers else 'None'}")
    except Exception as e:
        results.append(("Model Router", False))
        print(f"  ❌ Router failed: {e}")
    
    # 4. Tool Registry
    print("\n🔧 Testing Tool Registry...")
    try:
        registry = ToolRegistry(agent)
        tools = registry.list_tools()
        results.append(("Tool Registry", len(tools) > 0))
        print(f"  ✅ {len(tools)} tools registered: {', '.join(list(tools.keys())[:5])}")
    except Exception as e:
        results.append(("Tool Registry", False))
        print(f"  ❌ Tool registry failed: {e}")
    
    # 5. Session Manager
    print("\n👥 Testing Session Manager...")
    try:
        manager = SessionManager()
        session = manager.create()
        results.append(("Session Manager", session is not None))
        print(f"  ✅ Session created: {session.session_id[:8]}...")
    except Exception as e:
        results.append(("Session Manager", False))
        print(f"  ❌ Session manager failed: {e}")
    
    # 6. Basic chat
    print("\n💬 Testing basic chat...")
    try:
        response = agent.chat("Hello")
        results.append(("Basic chat", len(response) > 0))
        print(f"  ✅ Response received: {response[:50]}...")
    except Exception as e:
        results.append(("Basic chat", False))
        print(f"  ❌ Chat failed: {e}")
    
    # 7. Memory
    print("\n💾 Testing memory...")
    try:
        agent.memory.store("test", {"msg": "hello"})
        stats = agent.memory.get_stats()
        results.append(("Memory", stats['total_events'] > 0))
        print(f"  ✅ Memory working: {stats['total_events']} events stored")
    except Exception as e:
        results.append(("Memory", False))
        print(f"  ❌ Memory failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed_flag in results:
        status = "✅" if passed_flag else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Passed: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Local Agent v4.0 is ready!")
        print("\n🚀 Start the web server:")
        print("   python -m local_agent.web.app")
        print("\n🌐 Open browser:")
        print("   http://localhost:8000")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
