# lmi CLI Specification: Configuration and Environment Management

## Scope and Rationale

This specification details the configuration system for the `lmi` CLI, including supported sources, precedence rules, environment selection, and management. The goal is to provide a flexible, predictable, and secure configuration experience for users and developers.

## Detailed Requirements and Design

### 1. Configuration Sources
- Supported sources:
  1. Command-line arguments (highest precedence)
  2. OS environment variables
  3. Environment-specific `.env` files (`~/.config/lmi/env/<env_name>.env`)
  4. Main config file (`~/.config/lmi/.env`)
  5. Built-in defaults (if any)
- All configuration files use standard dotenv format.
- Any configuration value may be set via any source, following the documented precedence.

### 2. Environment Management
- Environments are defined by `.env` files in `~/.config/lmi/env/`.
- The active environment is selected via `-e <env_name>`/`--environment <env_name>`.
- If not specified, default to `default_environment` in the main `.env` file.
- Error if neither is specified or found.
- Environment-specific config is merged with main config, respecting precedence.

### 3. Configuration Resolution
- On startup, the CLI resolves the effective configuration by merging all sources according to precedence.
- Missing required config (with no default) results in a clear, actionable error.
- Secrets (e.g., client secrets) should be sourced from OS environment variables or env-specific `.env` files. Storing secrets in the main `.env` or CLI args is discouraged.

### 4. Dynamic Reloading
- Configuration is loaded once at startup; dynamic reloading is not supported.

### 5. Security Considerations
- Users are responsible for securing their `.env` and token cache files.
- The CLI does not enforce or check file permissions.
- Users can review logs to see what configuration variables were used.

## Implementation Guidelines
- Use `python-dotenv` for loading `.env` files.
- Provide clear error messages for missing or invalid configuration.
- Document configuration precedence and environment management for users.
- Follow PEP 8 and use type hints.
- Test configuration loading and precedence logic.

## References to PRD Sections
- Functional Requirements: FR1.1, FR2, FR4, FR4.1, FR4.2
- Non-Functional Requirements: NFR5, NFR6, NFR8
- Design & Architecture
- Release Criteria / MVP
- Decisions on Open Technical Questions: Configuration Sources, File Security & Permissions

## Explicit Non-Requirements and Philosophy

- **No Config Schema/Validation:** The CLI does not enforce a schema or type validation for configuration values. All config values are treated as strings unless otherwise handled by consuming code.
- **No Effective Config Command:** There is no CLI command to list or describe the effective configuration. Users must inspect their config files and environment variables directly.
- **Config Error Handling:** Configuration errors (e.g., missing required values) are surfaced as exceptions with clear error messages.

## Sensitive Value Handling in Logs

- **Not Part of MVP:** Sensitive value handling in logs is not part of the MVP and will be ignored for now. There are no requirements or recommendations for redaction or omission at this stage.

## Implementation Guidelines
- Use `python-dotenv`