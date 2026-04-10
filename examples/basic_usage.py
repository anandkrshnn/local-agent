"""
Basic Usage Example - Local Agent v0.1.0
Demonstrates initializing the agent and sending a simple chat request.
"""

from localagent.agent import LocalAgent
from localagent.config import Config

def main():
    # Load default configuration
    config = Config()
    
    # Initialize the agent
    # Ensure Ollama is running and phi3:mini is pulled
    print("Initializing Local Agent...")
    agent = LocalAgent(config=config)
    
    # Simple chat interaction
    user_input = "Hello! What can you do for me securely?"
    print(f"\nUser: {user_input}")
    
    response = agent.chat(user_input)
    print(f"\nAgent: {response}")

if __name__ == "__main__":
    main()
