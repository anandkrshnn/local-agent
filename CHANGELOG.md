# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-14 - Official Release

### ✨ Production Foundation
- **Sovereign Vaults**: Multi-tenant AES-256 encrypted storage silos with secure password-based derivation.
- **Local Permission Broker (LPB)**: Core security engine with JIT token-based authorization and 60s TTL.
- **Governed Learning**: Added `PromotionPipeline` for candidate memory rule generation and human-in-the-loop promotion.
- **Policy Simulation**: Backtest engine to simulate policy impact against historical episodes before activation.
- **Airlock Gateway**: Zero-trust LLM isolation with automated interception of sensitive tool calls.
- **Immutable Audit Trail**: Tamper-evident trail of all agent actions, user approvals, and security tokens.

### 🛠️ Infrastructure & UX
- **Environment-Aware Core**: Full support for `LOCAL_AGENT_VAULT` and `LOCAL_AGENT_SANDBOX` for cross-platform stability.
- **Docker-First Deployment**: Streamlined distribution via `ghcr.io` and one-liner `docker-run.sh`.
- **Dashboard v1.0**: High-end cyber-glass UI for Command, Brain, and Compliance management.
- **Developer Ergonomics**: Canonicalized around `pyproject.toml` with a "Getting Started" example suite.

---

[0.1.0]: https://github.com/anandkrshnn/local-agent/releases/tag/v0.1.0
