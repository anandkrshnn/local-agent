# Release v0.1.0-SYNTHESIS 🛡️

## 🎯 "Star-Ready" Public Debut

This release marks the initial public launch of **Local Agent**, a security-first AI assistant designed to stay 100% on your machine while providing advanced tool automation through a **Just-in-Time Permission Broker**.

### 🔑 Key Features

*   **🛡️ Permission Broker (LPB)**: A secure airlock that evaluates every tool call intent before execution.
*   **🧠 Auto-Learning**: Intelligent pattern recognition that reduces confirmation fatigue after 8 successful user approvals.
*   **🔐 Cryptographic Tokens**: JWT-signed, single-use, 60-second expiry tokens for tool execution.
*   **📜 Immutable Audit Trail**: All agent actions and user approvals are logged to a tamper-evident storage.
*   **🧬 Semantic Memory**: Cross-session context recall powered by a local DuckDB + VSS engine.
*   **🩺 Diagnosis Tool**: New `local-agent diagnose` command to quickly verify your environment readiness.

### 📦 Installation

```bash
pip install https://github.com/anandkrshnn/local-agent/archive/refs/tags/v0.1.0.tar.gz
```

### ⚠️ Known Limitations (v0.1.0)

*   This is a working prototype. Avoid use for mission-critical system management.
*   Single-user only.
*   Requires [Ollama](https://ollama.ai/) running locally.

### 🗺️ Roadmap

*   v0.2.0: Encrypted memory vault (AES-256) and multi-model switcher.
*   v0.3.0: Lightweight Desktop (Tauri) and Mobile companion apps.

---
*Special thanks to the early pilot partners for the feedback that shaped the SYNTHESIS release.*
