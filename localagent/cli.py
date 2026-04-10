import sys
import argparse
import uvicorn
from localagent.agent import LocalAgent
from localagent.config import Config
from localagent.__init__ import __version__

def main():
    parser = argparse.ArgumentParser(description=f"Local Agent v{__version__} - Security-First AI Assistant")
    parser.add_argument("--version", action="version", version=f"localagent {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # 'chat' command
    chat_parser = subparsers.add_parser("chat", help="Start a CLI chat session")
    
    # 'serve' command
    serve_parser = subparsers.add_parser("serve", help="Start the web dashboard")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to run the dashboard on (default: 8000)")
    serve_parser.add_argument("--host", type=str, default="localhost", help="Host to run the dashboard on (default: localhost)")

    args = parser.parse_args()

    if args.command == "chat":
        run_chat()
    elif args.command == "serve":
        run_serve(args.host, args.port)
    else:
        parser.print_help()

def run_chat():
    config = Config()
    agent = LocalAgent(config=config)
    print(f"--- Local Agent CLI v{__version__} ---")
    print("Type 'exit' or 'quit' to end the session.")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input:
                continue
            
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")
        except KeyboardInterrupt:
            break
    
    agent.close()
    print("\nGoodbye!")

def run_serve(host, port):
    print(f"Starting Local Agent Dashboard on http://{host}:{port}...")
    from localagent.web.app import app
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
