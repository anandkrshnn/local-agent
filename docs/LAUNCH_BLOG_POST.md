# Building a Secure "Airlock" for Local AI Agents: The Permission Broker Pattern

![Banner](docs/cover.png)

## The Problem: The "All or Nothing" Security Trap

If you've played with local AI agents like AutoGPT or Open Interpreter, you've likely hit the same wall I did. You either:
1. **Lock them down** to the terminal: They can talk, but they can't *do* anything.
2. **Give them system access**: You cross your fingers and hope a hallucination doesn't `rm -rf` your home directory.
3. **Approve everything**: You spend your life clicking "Y" to 50 tiny file reads just to organize a folder.

**None of these work for production.** We need agents that are actually useful but cryptographically prevented from going rogue.

## Introducing: The Local Permission Broker (LPB)

I built **Local Agent** to demonstrate a new security pattern: the **Permission Broker**. 

Instead of giving the AI model a persistent shell, the model interacts with a "Broker." This Broker evaluates every single tool call request before it reaches the system.

### How it Works (The Trust Stack)

1. **Intent Evaluation**: The Broker calculates a risk score based on the operation and the resource (e.g., `READ` is lower risk than `DELETE`).
2. **Just-in-Time Tokens**: If approved, the Broker issues a single-use JWT token with a 60-second expiry.
3. **Sandbox Execution**: The Executor *only* runs the tool if the token is valid, hasn't been used, and was signed by the Broker.
4. **Auto-Learning (The "Magic" Bit)**: Confirmation fatigue is real. If you approve the same pattern 8 times (e.g., "Agent creates notes in the sandbox"), the Broker learns it's trusted and auto-approves it from then on.

## The Technical Core: Python + Ollama + DuckDB

The entire system runs **100% locally**. 

- **AI Model**: Served via Ollama (Phi-3, Llama 3.2, or Qwen 2.5).
- **Security Logic**: FastAPI-based broker backend.
- **Semantic Memory**: DuckDB with the VSS (Vector Similarity Search) extension allows the agent to "remember" your preferences across sessions without a cloud vector DB.
- **Audit Trail**: Every action is saved to a tamper-evident Merkle tree log.

## Why This Matters for the "Post-Application Era"

We are moving away from monolithic applications toward **Sovereign Agents**. These agents need a way to prove their hardware attestation and verify their execution environments.

Local Agent is the personal-scale reference implementation of the **PTV (Provenance, Trust, Verification) Protocol**. The same logic used here to keep your local files safe is being scaled to enterprise AI stacks for healthcare and finance.

## Try It Yourself (60-Second Setup)

If you have Ollama installed, you can be up and running in a minute:

```bash
git clone https://github.com/anandkrshnn/local-agent.git
cd local-agent
pip install -e .
ollama pull phi3:mini
local-agent serve
```

---

🛡️ **Get the code**: [github.com/anandkrshnn/local-agent](https://github.com/anandkrshnn/local-agent)

*I'm launching v0.1.0-SYNTHESIS this Tuesday. I'd love to hear your thoughts on the permission broker pattern!*
