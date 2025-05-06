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

## 3. Logging System
- **Description:**
  - Implement file and console logging using `logging` and `rich`.
  - Support verbosity flags and config-based log control.
- **Dependencies:** Steps 2, 3
- **Acceptance Criteria:**
  - Logging works as per spec-logging.md and PRD (FR7)
  - Log output is testable and configurable
- **Status:**
  - Completed: [DATE]
  - Summary: Added src/lmi/logging.py, integrated setup_logging in CLI, added CLI options for verbosity and file log control, ensured logs include timestamps, level, and source, and updated docs/tests as needed.

---

## 4. Authentication & Token Caching
- **Description:**
  - Implement OAuth Client Credentials and Password Grant flows.
  - Implement token caching, expiry check, and refresh on 401.
- **Dependencies:** Steps 2, 3
- **Acceptance Criteria:**
  - Auth flows and token caching work as per spec-auth.md and PRD (FR6, FR6.1)
  - Unit/integration tests for token acquisition, caching, and refresh

---

## 5. CLI Command Structure
- **Description:**
  - Implement CLI entry point using `click`.
  - Support global options, environment selection, and command parsing.
- **Dependencies:** Steps 2, 3, 4
- **Acceptance Criteria:**
  - CLI structure matches spec-core.md and PRD (FR9, FR13, FR14)
  - `lmi --help` and `lmi --version` work

---

## 6. Plugin System
- **Description:**
  - Integrate `pluggy` for plugin discovery and registration.
  - Provide `CliContext` and authenticated `httpx.Client` to plugins.
- **Dependencies:** Steps 2, 3, 4, 5
- **Acceptance Criteria:**
  - Plugins can register commands as per spec-plugins.md and PRD (FR8, FR10, FR11, FR15)
  - Example/test plugin loads and runs

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