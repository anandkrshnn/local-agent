# Contributing to Local Agent

First off, thank you for considering contributing to the Local Agent! It's people like you that make Local Agent such a great security-first tool.

## Philosophy

- **Local First**: No cloud dependencies.
- **Security First**: Default to denial.
- **Privacy First**: Your data stays on your machine.

## Code of Conduct

Help us keep the project open and inclusive. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs
- Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md).
- Include steps to reproduce the issue.
- Mention your OS and model (e.g., Llama 3 on Windows 11).

### Suggesting Enhancements
- Check the [Roadmap](README.md#roadmap) first.
- Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md).

### Pull Requests
1. Fork the repo and create your branch from `main`.
2. Install development dependencies: `pip install -e .[dev]`
3. Ensure your code follows the existing style (we use Black and isort).
4. Run tests in the `_development/` folder before submitting.
5. Update documentation if you're adding tools or features.

## Development Setup

```bash
git clone https://github.com/anandkrshnn/local-agent.git
cd local-agent
pip install -e .[dev]
```

## Licensing

By contributing, you agree that your contributions will be licensed under its MIT License.
