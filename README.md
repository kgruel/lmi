# lmi CLI

A unified Command Line Interface (CLI) for interacting with platform services, providing centralized configuration, authentication, logging, and an extensible plugin architecture.

## Features
- Flexible configuration loading (files, env vars, CLI args)
- OAuth authentication with token caching
- Unified logging (file and console)
- Extensible plugin system
- Output formatting (JSON)
- 100% test coverage for core

## Requirements
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended for environment management)

## Setup
```sh
uv venv
uv pip install -e .
```

## Running
```sh
python main.py
```

## Testing
```sh
pytest --cov
```

## Linting
```sh
uv pip install ruff
ruff check .
```

## Documentation
See `docs/development/` for implementation plan, specs, and PRD.
