# lmi CLI Specification: Core Architecture

## Scope and Rationale

This specification defines the core architecture of the `lmi` CLI, covering the executable, configuration loading, authentication orchestration, command structure, and foundational behaviors. It ensures the CLI is consistent, extensible, and aligned with the product vision.

## Detailed Requirements and Design

### 1. Executable
- The CLI must provide a command-line executable named `lmi`.
- The executable should be discoverable in the user's PATH after installation.

### 2. Configuration Loading
- Load global config from `~/.config/lmi/.env` (optional, standard dotenv format).
- Load environment-specific config from `~/.config/lmi/env/*.env` (dotenv format).
- Select active environment via `-e <env_name>`/`--environment <env_name>`, defaulting to `default_environment` in main `.env` if not set. Error if neither is specified.
- Configuration precedence (highest to lowest):
  1. Command-line arguments
  2. OS environment variables
  3. Env-specific `.env` file
  4. Main `.env` config file
  5. Built-in defaults (if any)
- Missing required config (with no default) results in a clear error.

### 3. Authentication Orchestration
- Automatic authentication based on resolved config (OAuth Client Credentials & Password grants).
- Token caching: cache tokens in `~/.cache/lmi/tokens/<env_name>.json` (or similar, OS conventions respected).
- Check for valid, non-expired cached token before requests.
- On 401 Unauthorized, discard cache, acquire new token, and retry once.

### 4. Command Structure
- Command structure: `lmi [global_options] <service_group> <action> [action_options]` (plugin-ready).
- Use `click` for CLI parsing and help system.
- Provide context-aware help via `--help` at all levels.
- Version reporting via `--version` (core and loaded plugin versions).
- **Input from STDIN:**
  - Commands that accept input data (e.g., JSON, YAML, or text) must support a `--file <path>` option, where `--file -` reads from STDIN.
  - When `--file -` is specified, the CLI reads input from STDIN (e.g., piped data or redirected file).
  - If both `--file` and positional arguments are provided, `--file` takes precedence for input data.
  - The CLI must provide clear error messages if STDIN is empty or input is invalid.
  - Plugins are encouraged to adopt the same convention for input data.

### 5. Plugin Readiness
- Use `pluggy` to discover/load plugin commands (via entry points).
- Plugins register their `click` command groups via a `pluggy` hook (`register_commands`).
- Provide pre-configured, authenticated `httpx.Client` to plugin commands.
- Provide a `CliContext` object to plugins (resolved config, logger, HTTP client, global flags).

## Implementation Guidelines
- Use Python 3.11+.
- Follow PEP 8 and use type hints.
- Structure the core as a distinct Python package, separate from plugins.
- Ensure minimal CLI startup time.
- Provide clear error messages and stack traces at high verbosity.
- Maintain 100% test coverage for the core package.

## References to PRD Sections
- Functional Requirements: FR1, FR1.1, FR2, FR4, FR4.1, FR4.2, FR6, FR6.1, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15
- Non-Functional Requirements: NFR1, NFR2, NFR3, NFR4, NFR5, NFR6, NFR7, NFR8
- Design & Architecture
- Release Criteria / MVP 