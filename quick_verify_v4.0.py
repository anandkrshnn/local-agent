"""Quick Verification Script for Local Agent v4.0"""

import os
import sys

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

try:
    print("🚀 Initializing Local Agent v4.0...")
    from local_agent.core.agent import LocalAgent
    
    agent = LocalAgent(verbose=False)
    
    print("📋 Checking System Status...")
    stats = agent.get_stats()
    
    print(f"✅ Memory initialized: {stats['memory']['total_events']} events")
    print(f"✅ Model Router status: {stats['model_router']['providers'][0]['name']} is {stats['model_router']['providers'][0]['available']}")
    
    print("\n💬 Testing Basic Chat (Small Tier)...")
    response = agent.chat("Hello, who are you?")
    print(f"🤖 Response: {response}")
    
    print("\n🔧 Testing Tool Registry...")
    tools = agent.tool_registry.list_tools()
    print(f"✅ Registered tools: {', '.join(tools.keys())}")
    
    print("\n🔍 Testing Web Search Rule...")
    response = agent.chat("search web for Local Agent v4.0")
    print(f"🤖 Response: {response[:100]}...")
    
    print("\n✅ Verification SUCCESSFUL!")
    
except Exception as e:
    print(f"\n❌ Verification FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
