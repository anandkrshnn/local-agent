from localagent.agent import LocalAgent

# Create and use a secure vault
# This will initialize storage and a security broker bound to this vault
agent = LocalAgent(vault_root="my_first_vault", password="mysecret123")

print("--- Sovereign Local Agent Getting Started ---")
response = agent.chat("Remember my secret project code is ALPHA-789")
print(f"Agent Response: {response}")

# Check memory recall: This illustrates the 'Governed Brain' functionality
# where memories are retrieved only if the PolicyEngine allows it.
ctx = agent.memory_service.get_governed_context("secret project code", {})
print("\nRecalled memories from Sovereign Vault:")
for m in ctx.get("memories", []):
    print(f"- {m.get('body')} (Confidence: {m.get('confidence')})")

agent.close()
