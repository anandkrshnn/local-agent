# Technical FAQ: Local Agent

## 🔒 Security

### How does the "Security Airlock" actually work?
The "Airlock" is an abstraction for the separation of concerns between **Intent Generation** (The AI Model) and **Action Execution** (The Tool Executor). The Model *never* calls a function. It sends a request to the **Local Permission Broker (LPB)**. Only if the LPB issues a cryptographically signed token can the Executor perform the I/O.

### Are tokens really single-use?
Yes. When the Executor receives a token, it hands it back to the Broker for validation. The Broker checks the signature and expiry, then immediately deletes the token from its `active_tokens` registry. This happens **before** the tool logic runs, making replay attacks with intercepted tokens impossible.

### What prevents "Prompt Injection" from deleting my files?
Even if a model is tricked into wanting to delete a file (e.g., via a malicious email summary), the request still has to go through the Broker. The Broker enforces:
1.  **Sandbox Whitelisting**: It only allows actions within the `~/LocalAgentSandbox` directory.
2.  **Explicit Tool Intent**: Deleting isn't a "free" action; it's a specific tool request that is flagged as **HIGH RISK**, always requiring manual user confirmation regardless of previous trust levels.

---

## 🧠 Memory & AI

### Why DuckDB instead of a server-side Vector DB?
Local Agent is built for privacy and low latency. Server-side Vector DBs (like Pinecone) require sending your data to a cloud. Even local Docker-based ones (like Milvus) are heavy and overkill. DuckDB with the VSS extension is an embedded file (`.duckdb`) that allows sub-millisecond similarity searches with zero configuration and zero networking.

### Which model is best for tool calling?
We recommend **Phi-3 Mini (3.8B)** or **Llama 3.2 (3B)**. These models are specifically fine-tuned for instruction following and reliably generate the structured JSON actions required by the ReAct loop. Larger models (70B) work but are significantly slower on consumer hardware.

---

## ⚡ Performance

### Will this slow down my computer?
Local Agent is designed to be lightweight.
- **Inference**: Handled by **Ollama**, which uses your GPU (Metal, CUDA) or CPU (AVX) efficiently.
- **Memory**: DuckDB uses minimal RAM (~50MB) and performs searches in the background.
- **Broker**: A thin Python layer that adds negligible overhead (~5ms).

---

## 🛠️ Usage

### Can I add my own tools?
Absolutely. Local Agent is designed to be extensible. You just need to create a Python class that inherits from the `Tool` base class and register it in `agent.py`.

### How do I reset the "Auto-Learning" trust?
Restart the agent. In the current version (v0.4.0), learned patterns are stored in-memory for security. This ensures each session starts with a clean security profile.
