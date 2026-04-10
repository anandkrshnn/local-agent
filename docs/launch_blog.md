# Building Trustworthy Local AI Agents: The Permission Broker Pattern

*Or: How I learned to stop worrying and let my AI agent use tools.*

---

## 🛡️ The Problem: The Agency Dilemma

To be useful, an AI needs to *do things*. It needs to organize your filesystem, summarize your meetings, manage your calendar, and perhaps even automate your workflows. In technical terms, it needs **tools**.

But there’s a problem: **most local agents are either useless or dangerous.**

### The Usefulness Trap
An AI agent that can only chat is a toy. To transition from "chatbot" to "assistant," the model must interact with the real world. It needs `read_file`, `write_file`, `execute_shell`, and `make_api_call`.

### The Danger Trap
The moment you give a Large Language Model (LLM) system-level access, you’ve created a security nightmare. LLMs are non-deterministic. They hallucinate. And more dangerously, they are susceptible to **Prompt Injection**. 

### The Confirmation Hell Trap
If I have to click "Approve" ten times to let the agent create a simple directory structure, I might as well have done it myself.

---

## ✨ The Solution: The Local Permission Broker (LPB) Pattern

**Local Agent** is an open-source assistant designed to solve this exact problem. The core innovation is the **Local Permission Broker (LPB)**.

The LPB acts as a **Security Airlock**. The model never touches your system directly. Instead, it must declare its *intent* to a broker, which evaluates the request against a policy, assesses risk, and issues a cryptographic, single-use token.

### Layer 1: Intent, Not Execution
The model generates a structured **Intent Declaration** (JSON).

### Layer 2: The Broker's Decision Engine
The Broker performs three checks:
1.  **Whitelisting**: Is the file path in `sandbox/`?
2.  **Risk Assessment**: Read vs Write.
3.  **Learned Trust**: Bayesian-inspired trust threshold (8 approvals / 24h).

### Layer 3: The Single-Use Token
If approved, the Broker issues a **Cryptographic Token** (HMAC-SHA256, 60s expiry).

### Layer 4: The Executor & Sandbox
The **Tool Executor** consumes the token **before** execution, preventing reuse.

---

## 🧠 Semantic Memory: Why DuckDB VSS?

We chose **DuckDB with the VSS extension** for privacy and performance.
- **Zero Latency**: Embedded database.
- **Privacy Core**: Embeddings (`all-MiniLM-L6-v2`) and storage are 100% local.
- **SQL Power**: Hybrid search (semantic + metadata).

---

## 🛡️ The Hallucination Guard

In `agent.py`, we implemented a strict **Hallucination Guard**. If a model tries to use a non-existent tool, the observation is corrected before the model continues thinking.

---

## 🏛️ The Philosophy of Sovereign Intelligence

"Digital Sovereignty" requires that your intelligence layer stays under your control. By airlocking the model with the LPB, we prove that you can have a capable, agentic AI that is 100% private.

**Try Local Agent today:**
```bash
pip install -e .
ollama pull phi3:mini
local-agent serve
```

**Repository**: [https://github.com/yourusername/local-agent](https://github.com/yourusername/local-agent)
