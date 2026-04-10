# Security Policy

## Supported Versions

Currently, only the latest version of **Local Agent** (v0.1.x) is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| v0.1.x  | :white_check_mark: |
| < v0.1  | :x:                |

## Reporting a Vulnerability

**Local Agent** is a security-first project. We take every report seriously.

If you find a security vulnerability, please **DO NOT** open a public issue. Instead, please report it via one of the following methods:

1. **GitHub Private Reporting**: Use the "Report a security vulnerability" button on the [Security tab](https://github.com/anandkrshnn/local-agent/security).
2. **Email**: [Add your email or instructions here]

### Our Response Process

- We will acknowledge your report within 48 hours.
- We will provide a preliminary assessment of the risk.
- We will work on a fix and keep you updated on the progress.
- Once fixed, we will publish the fix and credit you (if desired).

## Security Guarantees

Local Agent is designed with the following core security principles:

1. **Just-In-Time Tokens**: No persistent tool access. 
2. **Short-Lived Permissions**: Tokens expire after 60 seconds.
3. **Single-Use**: Each token can only be consumed once.
4. **Environment Isolation**: Execution happens in a dedicated sandbox directory.
5. **Transparency**: All requests and outcomes are logged to a tamper-evident audit trail.

Thank you for helping keep Local Agent safe!
