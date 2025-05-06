# Development Guide

Guidance for contributors and maintainers, including project structure, testing, and coding standards for **lmi**.

## 1. Project Structure

- Source code: `src/`
- Tests: `tests/` (mirrors source structure)
- Docs: `docs/`
- Config/specs: `docs/development/specs/`

## 2. Running Tests

- Use `pytest` to run all tests:
  ```sh
  pytest
  ```
- Ensure 100% test coverage for the core package.
- Use `coverage.py` or equivalent to measure coverage.

## 3. Coding Standards

- Follow [PEP 8](https://peps.python.org/pep-0008/) for code style.
- Use type hints throughout the codebase.
- Write descriptive test names and docstrings.

## 4. Contributing

- Fork the repository and create a feature branch.
- Write or update tests for your changes.
- Ensure all tests pass and coverage is maintained.
- Open a pull request with a clear description of your changes.
- For plugin development, see the plugin system documentation and example plugins. 