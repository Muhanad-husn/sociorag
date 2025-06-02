# Contributing to SocioRAG

Thank you for your interest in contributing to SocioRAG! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/sociorag.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Set up the development environment (see DEPLOYMENT.md)

## 📋 Development Process

### Code Style
- Follow PEP 8 for Python code
- Use type hints where applicable
- Write descriptive docstrings
- Keep functions focused and modular

### Testing
- Write tests for new features
- Ensure all tests pass: `pytest tests/ -v`
- Maintain test coverage above 80%
- Test both English and Arabic language features

### Documentation
- Update documentation for new features
- Include examples in docstrings
- Update README.md if needed

## 🔧 Pull Request Process

1. **Create a descriptive title** and detailed description
2. **Reference any related issues** using `#issue-number`
3. **Ensure all tests pass** and coverage is maintained
4. **Update documentation** as needed
5. **Request review** from maintainers

### PR Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] Branch is up to date with main

## 🐛 Bug Reports

When reporting bugs, please include:
- **Environment details** (OS, Python version, etc.)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error logs** or stack traces
- **Sample data** if applicable (anonymized)

## 💡 Feature Requests

For new features, please provide:
- **Clear description** of the feature
- **Use case** and business justification
- **Proposed implementation** approach
- **Potential impact** on existing functionality

## 📝 Commit Messages

Use clear, descriptive commit messages:
```
feat: add Arabic translation support
fix: resolve vector search performance issue
docs: update API documentation
test: add integration tests for PDF export
```

## 🏷️ Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## 📞 Questions?

- Open an issue for general questions
- Check existing documentation in `docs/`
- Review the project status in `docs/project_status.md`

Thank you for contributing to SocioRAG! 🎉
