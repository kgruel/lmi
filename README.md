# lmi CLI

A unified Command Line Interface (CLI) for interacting with platform services. `lmi` centralizes configuration, authentication, logging, and provides an extensible plugin architecture for integrating service-specific commands. Designed for developers and operators, it simplifies workflows, enables automation, and ensures a consistent user experience.

## Features
- Flexible configuration loading (files, env vars, CLI args) with clear precedence
- Automated OAuth2 authentication (Client Credentials & Password Grant) with token caching and refresh
- Unified logging (file + rich console, configurable verbosity)
- Extensible plugin system (install, uninstall, list, discover via entry points)
- Output formatting (JSON, script-friendly)
- 100% test coverage for core

## Requirements
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended for environment management)

## Installation & Setup
```sh
uv venv
uv pip install -e .
```
The CLI is installed as `lmi` (see `pyproject.toml`).

## Configuration
- Config sources (highest to lowest precedence):
  1. CLI arguments
  2. OS environment variables
  3. `~/.config/lmi/env/<env>.env`
  4. `~/.config/lmi/.env`
- Select environment with `-e <env_name>` or set `default_environment` in `.env`.
- Secrets (e.g., client secrets) should be set via env vars or env-specific `.env` files.

## Authentication
- Supports OAuth2 Client Credentials & Password Grant flows
- Tokens cached in `~/.cache/lmi/tokens/<env>.json`
- Automatic token refresh on 401 Unauthorized

## Logging
- File logs: `~/.local/share/lmi/lmi.log` (configurable, disable with `--no-file-log`)
- Console logs: rich formatting, verbosity with `-v` (INFO), `-vv` (DEBUG)

## Usage Examples

### Basic CLI
```sh
lmi --help
lmi --version
lmi -e dev --output json <command> [options]
```

### Plugin Management
```sh
lmi plugin install my-plugin
lmi plugin uninstall my-plugin
lmi plugin list
```

### Example: Running a Plugin Command
```sh
lmi myplugin do-something --option value
```
*Assumes a plugin named `myplugin` is installed and registered.*

### Example: Scripting with JSON Output
```sh
lmi -e staging myplugin get-data --output json | jq .
```

## Plugin System
- Plugins are Python packages discovered via the `lmi_plugins` entry point.
- Plugins register commands using a `pluggy` hook and receive a context with config, logger, and authenticated HTTP client.
- See `docs/development/specs/spec-plugins.md` for developer details.

## Testing & Linting
```sh
pytest --cov
uv pip install ruff
ruff check .
```

## Documentation
See `docs/development/` for implementation plan, specifications, and PRD:
- `spec-core.md`: Core CLI architecture, configuration, authentication, command structure
- `spec-plugins.md`: Plugin system, lifecycle, extension interface
- `spec-logging.md`: Logging, error handling, output formatting
- `spec-config.md`: Configuration sources, precedence, environment management
- `spec-auth.md`: OAuth authentication flows, token caching, refresh logic
- `spec-testing.md`: Testing requirements, coverage, quality standards
