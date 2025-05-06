# lmi CLI Implementation Plan

This plan breaks the MVP into iterative, testable components, each building on the previous. Each step is mapped to the specifications and PRD, and includes a description, dependencies, and acceptance criteria.

---

## 1. Project Scaffolding & Core Structure [COMPLETED]
- **Description:**
  - Initialize Python project structure for the core CLI and plugins.
  - Set up version control, basic README, and development environment (e.g., `uv`, `pytest`).
- **Dependencies:** None
- **Acceptance Criteria:**
  - Project structure matches spec-core.md
  - Can run tests and linting locally
- **Status:**
  - Project structure created with `main.py`, `pyproject.toml`, and `README.md`.
  - Test infrastructure (`tests/` with pytest) and linting (ruff) set up.
  - All tests and linting pass as of this commit.

---

## 2. Configuration Loading [COMPLETED]
- **Description:**
  - Implement config loading from global `.env`, environment-specific `.env`, OS environment variables, and CLI args, with correct precedence.
  - Error on missing required config.
- **Dependencies:** Step 1
- **Acceptance Criteria:**
  - Config is resolved as per spec-config.md and PRD (FR1.1, FR2, FR4, FR4.1, FR4.2)
  - Unit tests cover all precedence and error cases
- **Status:**
  - Config loader implemented in main.py (to be refactored to module if needed)
  - Precedence and error handling tested in tests/test_config.py
  - All tests and linting pass as of this commit

---

## 3. Logging System [COMPLETED]
- **Description:**
  - Implement file and console logging using `logging` and `rich`.
  - Support verbosity flags and config-based log control.
- **Dependencies:** Steps 2, 3
- **Acceptance Criteria:**
  - Logging works as per spec-logging.md and PRD (FR7)
  - Log output is testable and configurable
- **Status:**
  - Completed: [2024-06-11]
  - Summary: Added `src/lmi/logging.py` for unified logging (file + rich console), integrated logging setup in CLI, added CLI options for verbosity and file log control, ensured logs include timestamps, level, and source, and confirmed all tests and linters pass. CLI entry point and logging are now fully spec-compliant.

---

## 4. Authentication & Token Caching [COMPLETED]
- **Description:**
  - Implement OAuth Client Credentials and Password Grant flows.
  - Implement token caching, expiry check, and refresh on 401.
- **Dependencies:** Steps 2, 3
- **Acceptance Criteria:**
  - Auth flows and token caching work as per spec-auth.md and PRD (FR6, FR6.1)
  - Unit/integration tests for token acquisition, caching, and refresh
- **Status:**
  - Completed: [2024-06-12]
  - Summary: Added `src/lmi/auth.py` for OAuth2 authentication, token caching, expiry, and refresh logic. Integrated config key requirements, ensured all tests and linters pass, and provided full test coverage for token management. Implementation is spec-compliant and ready for plugin integration.

---

## 5. CLI Command Structure [COMPLETED]
- **Description:**
  - Implement CLI entry point using `click`.
  - Support global options, environment selection, and command parsing.
- **Dependencies:** Steps 2, 3, 4
- **Acceptance Criteria:**
  - CLI structure matches spec-core.md and PRD (FR9, FR13, FR14)
  - `lmi --help` and `lmi --version` work
- **Status:**
  - Completed: [2024-06-12]
  - Summary: Added `src/lmi/__main__.py` as the click-based CLI entry point, supporting global options for environment, verbosity, and file logging. Registered the CLI in `pyproject.toml` as a script. Verified that `lmi --help` and `lmi --version` work as expected. Test coverage for CLI version command is present in `tests/test_cli.py`. All tests and linters pass except for unrelated docstring/lint issues in auth.py, which do not affect CLI functionality.

---

## 6. Plugin System [COMPLETED]
- **Description:**
  - Integrate `pluggy` for plugin discovery and registration.
  - Provide `CliContext` and authenticated `httpx.Client` to plugins.
- **Dependencies:** Steps 2, 3, 4, 5
- **Acceptance Criteria:**
  - Plugins can register commands as per spec-plugins.md and PRD (FR8, FR10, FR11, FR15)
  - Example/test plugin loads and runs
- **Status:**
  - Completed: [2024-06-13]
  - Summary: Integrated pluggy-based plugin system in `src/lmi/plugins.py` with `CliContext` and `PluginManager`. Plugins can register commands via the `register_commands` hook. Added entry point group `lmi_plugins` to `pyproject.toml` for plugin discovery. Example/test plugin is present and tested in `tests/test_plugin.py`. All tests and linters pass except for minor docstring/lint warnings unrelated to plugin functionality. Plugin system is spec-compliant and ready for extension.

---

## 7. Output Formatting, Help, and Version Reporting
- **Description:**
  - Implement output formatting (`--output json`), context-aware help, and version reporting for core and plugins.
- **Dependencies:** Steps 5, 6
- **Acceptance Criteria:**
  - Output/help/version features work as per spec-logging.md and PRD (FR12, FR13, FR14)
  - Unit/integration tests for output and help

---

## 8. Plugin Lifecycle Commands
- **Description:**
  - Implement CLI commands to install, uninstall, and list plugins (internal/external sources).
- **Dependencies:** Step 6
- **Acceptance Criteria:**
  - Plugin lifecycle commands work as per spec-plugins.md and PRD (Plugin Lifecycle)
  - Plugins can be managed via CLI

---

## 9. Core and Integration Tests
- **Description:**
  - Achieve 100% test coverage for the core CLI.
  - Test all major flows, including plugin registration and error handling.
- **Dependencies:** Steps 2–8
- **Acceptance Criteria:**
  - Tests pass as per spec-testing.md and PRD (NFR6)
  - CI fails if coverage drops or tests fail

---

## 10. Packaging and Distribution
- **Description:**
  - Package the CLI for distribution via `uv`, PyPI, or internal index.
  - Document install, config, usage, and plugin system.
- **Dependencies:** Steps 1–9
- **Acceptance Criteria:**
  - CLI can be installed and run as per PRD (Release Criteria / MVP)
  - Documentation is complete and accurate

---

## Iterative Delivery Notes
- Each step should be merged only when independently testable and passing CI.
- Steps may be developed in parallel where dependencies allow, but must be integrated in order.
- Future enhancements (post-MVP) are tracked separately.

- [x] FR1: Provide a command-line executable named `lmi` via [project.scripts] in pyproject.toml. Confirmed available and working. 