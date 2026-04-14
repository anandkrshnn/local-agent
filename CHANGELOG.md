# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-04-14

### Added
- **Sovereign Vaults**: AES-256 encrypted storage silos with secure password-based derivation and key rotation.
- **Governed Learning**: Added `PromotionPipeline` for candidate memory rule generation and human-in-the-loop promotion.
- **Policy Simulation**: Backtest engine to simulate policy impact against historical episodes before activation.
- **Cross-Platform Hardening**: Refactored core path management via `VaultContext` to support environment-aware deployment (`LOCAL_AGENT_VAULT`, `LOCAL_AGENT_SANDBOX`).
- **Visual Architecture**: Integrated Mermaid-based security diagrams and high-fidelity demo assets.

### Changed
- **CI/CD Overhaul**: Refactored GitHub Actions for automated Docker builds and publication to `ghcr.io`.
- **Repo Hygiene**: Streamlined repository by removing legacy `frontend/`, `requirements.txt`, and `setup.py`, canonicalizing all build logic in `pyproject.toml`.
- **Security Posture**: Hardened LPB (Local Permission Broker) with improved resource normalization and better error handling.
- **Onboarding**: Added `examples/getting_started.py` for immediate developer onboarding.

---

## [0.1.0] - 2026-04-10

### Added
- **Local Permission Broker (LPB)**: Core security engine with JIT token-based authorization.
- **Semantic Memory Engine**: DuckDB-powered vector memory for conceptual recall.
- **Secure Sandbox**: Path-restricted file execution environment.
- **Audit Logging**: Immutable SQLite trail of all agent actions and user approvals.
- **Web Dashboard**: Real-time interface for chat and permission management.
- **CLI Interface**: Command-line tools for local interaction.

### Changed
- Initial public release and repository standardization.
- Hardened token TTL to 60 seconds.
- Simplified dependency chain for lightweight local-first operation.

---

[0.3.0]: https://github.com/anandkrshnn/local-agent/releases/tag/v0.3.0
[0.1.0]: https://github.com/anandkrshnn/local-agent/releases/tag/v0.1.0
