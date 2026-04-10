"""
Basic Usage Example for localagent
Demonstrating the LocalPermissionBroker (LPB) security airlock.
"""

import os
from localagent import LocalAgent

def main():
    # 1. Initialize the agent (Defaults to Phi-3 mini via Ollama)
    agent = LocalAgent()
    
    print("🤖 Local Agent Usage Example")
    print("----------------------------")
    
    # 2. Simple chat interaction
    print("\n👤 > Hello! Who are you?")
    response = agent.chat("Hello! Who are you?")
    print(f"🤖 {response}")
    
    # 3. Secure tool execution (File read)
    # This will trigger the broker to issue an ephemeral token
    print("\n📦 Attempting to read a file in the sandbox...")
    # First, let's write a file to the sandbox for testing
    agent.sandbox.secure_write("test.txt", "This is a secret message for the agent.")
    
    # Execute tool via the agent's secure interface
    tool_result = agent.execute_tool("read_file", {"path": "test.txt"})
    print(f"📦 Tool Result: {tool_result}")
    
    # 4. High-risk tool execution (Triggering confirmation)
    print("\n⚠️ Attempting a write operation (requires confirmation)...")
    confirmation_res = agent.execute_tool("write_file", {"path": "output.txt", "content": "Proof of access."})
    print(f"⚠️ Broker Response: {confirmation_res}")
    
    # Check stats for audit integrity
    print("\n📊 Current Audit Stats:")
    print(agent.get_stats()["broker"])

if __name__ == "__main__":
    main()
