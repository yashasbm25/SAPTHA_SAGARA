# CONTRIBUTING.md

## Code of Conduct

Be respectful, inclusive, and constructive.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Make changes
5. Run tests: `pytest tests/`
6. Commit with clear messages
7. Push to your fork
8. Create a Pull Request to `dev` branch

## Development Setup

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

## Code Style

**Python:**
- PEP 8 with Black formatter
- Type hints required
- Docstrings for all functions

**TypeScript/React:**
- ESLint configuration
- Prettier for formatting
- Props interfaces for all components

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, perf, test, chore

Example:
```
feat(risk-engine): add lightning alert scoring

Implement deterministic scoring for lightning alerts
as a factor in the risk assessment algorithm.

Closes #123
```

## Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers
6. Address feedback
7. Squash commits before merge

## Architecture Guidelines

- Keep agents focused and single-responsibility
- Use provider abstraction for data sources
- Never hardcode API endpoints
- Normalize data to common schema
- Always track data freshness
- Implement graceful fallbacks
- Log all errors

## Testing Requirements

- Unit tests for business logic
- Integration tests for API endpoints
- Mock external API calls
- Test edge cases and error paths
- Aim for >80% coverage

## Issues & Discussions

- Report bugs with reproduction steps
- Suggest features with use cases
- Ask questions in discussions
- Label issues appropriately

## Release Process

1. Update version in package files
2. Update CHANGELOG.md
3. Create release branch
4. Tag commit with version
5. Merge to main
6. Create GitHub release
7. Deploy to production
