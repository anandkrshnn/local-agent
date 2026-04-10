# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/anandkrshnn/local-agent/releases/tag/v0.1.0
