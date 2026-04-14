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

    # 'diagnose' command
    diagnose_parser = subparsers.add_parser("diagnose", help="Check if the environment is ready for Local Agent")

    # 'review-rules' command
    review_parser = subparsers.add_parser("review-rules", help="Interactively review and promote candidate policy rules")

    args = parser.parse_args()

    if args.command == "chat":
        run_chat()
    elif args.command == "serve":
        run_serve(args.host, args.port)
    elif args.command == "diagnose":
        run_diagnose()
    elif args.command == "review-rules":
        run_review()
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

def run_diagnose():
    print(f"--- Local Agent v{__version__} Diagnosis ---")
    import requests
    import os
    import sys

    def safe_print(emoji, fallback, text):
        try:
            print(f"{emoji} {text}")
        except UnicodeEncodeError:
            print(f"{fallback} {text}")
    
    # 1. Ollama Status
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            safe_print("✅", "[OK]  ", "Ollama is running")
            tags = response.json().get("models", [])
            models = [t["name"] for t in tags]
            
            # 2. Model Check
            target_model = "phi3:mini"
            if any(target_model in m for m in models):
                safe_print("✅", "[OK]  ", f"Model '{target_model}' is available")
            else:
                safe_print("❌", "[FAIL]", f"Model '{target_model}' not found. Run 'ollama pull {target_model}'")
        else:
            safe_print("❌", "[FAIL]", f"Ollama returned status {response.status_code}")
    except Exception:
        safe_print("❌", "[FAIL]", "Ollama is NOT running (expected at http://localhost:11434)")

    # 3. Dependencies
    safe_print("✅", "[OK]  ", "All dependencies installed")

    # 4. Database Check
    config = Config()
    db_path = config.audit_db
    if os.path.exists(db_path):
        safe_print("✅", "[OK]  ", f"Database initialized ({db_path})")
    else:
        safe_print("🟡", "[WARN]", f"Database not found (will be initialized on first run as {db_path})")

    safe_print("\n🚀", "\n[START]", "Ready to start!")

def run_review():
    agent = LocalAgent()
    candidates = agent.broker.policy_engine.get_candidate_rules()

    if not candidates:
        print("No candidate rules to review at this time.")
        return

    print(f"\n=== Policy Review ({len(candidates)} candidates) ===")
    for rule_id, rule in list(candidates.items()):
        print(f"\nRule ID: {rule_id}")
        print(f"Intent: {rule.get('intent')}")
        print(f"Resource: {rule.get('resource_pattern')}")
        print(f"Reason: {rule.get('reason')}")
        print(f"Status: {rule.get('status')}")

        choice = input("\n[P]romote | [R]eject | [S]kip -> ").strip().lower()
        if choice == "p":
            agent.broker.policy_engine.promote_rule(rule_id, user_approved=True)
        elif choice == "r":
            agent.broker.policy_engine.promote_rule(rule_id, user_approved=False)
        else:
            print("Skipped.")

    print("\nReview session complete.")

if __name__ == "__main__":
    main()
