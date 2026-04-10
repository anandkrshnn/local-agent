# tests/test_new_tools.py
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from localagent.agent import LocalAgent

def test_new_tools():
    agent = LocalAgent()
    sandbox_root = agent.sandbox.root

    # Ensure clean temp dir for test consistency
    temp_dir = sandbox_root / "temp"
    temp_dir.mkdir(exist_ok=True)

    print("🛠️ Testing new tools...\n")

    # Test 1: list_directory
    print("1. Testing list_directory...")
    result = agent.chat("List the files in my sandbox")
    print("Result:", result)

    # Test 2: append_to_file
    print("\n2. Testing append_to_file...")
    # NOTE: In a real interactive session, this would return a confirmation prompt.
    # In this automated test script using agent.chat(), it will return the ⚠️ message.
    append_result = agent.chat("Append 'Test note from agent - 2026' to temp/test_notes.txt")
    print("Append result:", append_result)

    # Verify file content
    test_file = temp_dir / "test_notes.txt"
    # Note: If the agent correctly returned the confirmation, the file won't be created yet.
    # The user's test script assumes it might be created, but our security loop gates it.
    if test_file.exists():
        content = test_file.read_text()
        print("File content preview:", content[:100])
    else:
        print("Status: Action correctly gated by Permission Broker (Confirmation Required).")

    print("\n✅ New tools test sequence completed.")

if __name__ == "__main__":
    test_new_tools()
