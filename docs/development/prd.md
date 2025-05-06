# lmi - Unified Platform CLI

**Product Requirements Document (PRD)**  
Version: 1.2  
Date: May 5, 2025

---

## Table of Contents
1. [Introduction](#introduction)
2. [Goals](#goals)
3. [Non-Goals (Initial Scope)](#non-goals-initial-scope)
4. [Target Audience](#target-audience)
5. [Use Cases](#use-cases)
6. [Requirements](#requirements)
    - [Functional Requirements](#functional-requirements)
    - [Non-Functional Requirements](#non-functional-requirements)
7. [Design & Architecture](#design--architecture)
8. [Release Criteria / Minimum Viable Product (MVP)](#release-criteria--minimum-viable-product-mvp)
9. [Future Considerations](#future-considerations)
10. [Decisions on Open Technical Questions](#decisions-on-open-technical-questions-may-2025)
11. [Remaining Open Questions](#remaining-open-questions)

---

## 1. Introduction

**Problem:**
> Interacting with the company's suite of platform services (e.g., OAuth, Accounts, Client Management, External Admin) currently requires developers to consult multiple documentation sources, use different tools/APIs, and manually handle configuration and authentication boilerplate for each service and environment. This process is inefficient, error-prone, hard to script, and increases onboarding time.

**Proposed Solution:**
> `lmi` is a unified Command Line Interface (CLI) designed to provide a single, consistent entry point for interacting with these platform services. It centralizes configuration, authentication, and logging, while offering an extensible plugin architecture for integrating service-specific commands.

**Vision:**
> `lmi` will become the standard, scriptable tool for developers and operators interacting with core platform services, simplifying workflows and improving productivity.

---

## 2. Goals
- **Simplify Interaction:** Single CLI tool for multiple platform services.
- **Flexible Configuration:** Manage details via files, environment variables, and CLI arguments with clear precedence.
- **Streamline Authentication:** Automate OAuth flows, including token caching and refresh.
- **Improve Discoverability:** Built-in help for services and commands.
- **Enable Automation:** Script single-service and cross-service workflows.
- **Reduce Onboarding Time:** Lower the barrier for new users.
- **Consistent UX:** Predictable command structure and user experience.

---

## 3. Non-Goals (Initial Scope)
- No GUI or web UI.
- No built-in workflow engine (users script via shell/other tools).
- No management of underlying infrastructure or platform service deployment.
- Not replacing detailed service-specific API documentation.
- No direct database/backend storage interaction (must use official APIs).
- No real-time monitoring or dashboards.

---

## 4. Target Audience
- Platform Engineers (developing/operating core services)
- Product/Application Developers (consuming platform services)
- Support/Operations Teams (routine tasks, debugging)
- *(No specific teams prioritized for initial MVP rollout)*

---

## 5. Use Cases
- **UC1 (Environment Switching & Auth):**
  - Alice uses config files like `~/.config/lmi/env/ed1.env` (Client Credentials) and `~/.config/lmi/env/dev-user.env` (Password Grant).
  - She runs `lmi -e ed1 ...` and `lmi -e dev-user ...` to switch environments, verifying authentication and token caching/refresh.
- **UC2 (Client Management):**
  - *(Future plugin)* Bob registers a new OAuth client for "Analytics" in staging using a `clientmgr` plugin.
- **UC3 (Environment Config & Override):**
  - Alice creates `~/.config/lmi/env/stage.env`, sets `OAUTH_SERVICE_URL`, overrides with an env var, and disables file logging in the main `.env`.
- **UC4 (Discovery):**
  - Carol runs `lmi --help` to see available commands and options, including plugin commands if installed.
- **UC5 (Scripting Core Functions):**
  - Bob scripts over all env files in `~/.config/lmi/env/`, running commands with `-e <env_name>`, relying on cached tokens.

---

## 6. Requirements

### Functional Requirements

#### Core (`lmi`)
- **FR1:** Provide a command-line executable named `lmi`.
- **FR1.1:** Load global config from `~/.config/lmi/.env` (standard `.env` format, optional).
- **FR2:** Load environment-specific config from `~/.config/lmi/env/*.env` (standard `.env` format).
- **FR4:** Select active environment via `-e <env_name>`/`--environment <env_name>`, defaulting to `default_environment` in main `.env` if not set. Error if neither is specified.
- **FR4.1:** Config precedence (highest to lowest):
  1. Command-line arguments (e.g., `--oauth_service_url ...`)
  2. OS environment variables (e.g., `export OAUTH_CLIENT_SECRET=...`)
  3. Env-specific `.env` file (e.g., `~/.config/lmi/env/ed1.env`)
  4. Main `.env` config file
  5. Built-in defaults (if any)
- **FR4.2:** Missing required config (with no default) results in a clear error.
- **FR6:** Automatic authentication based on resolved config (OAuth Client Credentials & Password grants). Other flows (e.g., Auth Code + PKCE) are future work.
- **FR6.1:** Automatic OAuth token caching:
  - Cache tokens in `~/.cache/lmi/tokens/<env_name>.json` (or similar, OS conventions respected).
  - Check for valid, non-expired cached token before requests.
  - On 401 Unauthorized, discard cache, acquire new token, and retry once.
- **FR7:** Unified logging:
  - File logs (default: `~/.local/share/lmi/lmi.log` or `%LOCALAPPDATA%\lmi\lmi.log` on Windows). Can be disabled/configured.
  - Console logs to STDERR via `rich.logging.RichHandler`. Verbosity: `-v` (INFO), `-vv` (DEBUG). Can be disabled/configured.
- **FR8:** Use `pluggy` to discover/load plugin commands (via entry points).
- **FR9:** Command structure: `lmi [global_options] <service_group> <action> [action_options]` (plugin-ready).
- **FR10:** Provide pre-configured, authenticated `httpx.Client` to plugin commands (handles token injection/refresh).
- **FR11:** Provide a `CliContext` object to plugins (resolved config, logger, HTTP client, global flags).
- **FR12:** Output formatting via `--output <format>`. JSON required (default). Output to STDOUT.
- **FR13:** Context-aware help via `--help` at all levels (root, service group, action) using `click`.
- **FR14:** Version reporting via `--version` (core and loaded plugin versions).
- **FR15:** Plugins register their `click` command groups via a `pluggy` hook (`register_commands`).
- **FR16:** Commands that accept input data (e.g., JSON, YAML, or text) must support a `--file <path>` option, where `--file -` reads from STDIN. The CLI must provide clear error messages if STDIN is empty or input is invalid. Plugins are encouraged to follow the same convention.
- **Plugin Lifecycle:** CLI must provide commands to install, uninstall, and list plugins (supporting internal/external repos as configured).

### Non-Functional Requirements
- **NFR1 (Usability):** Consistent, intuitive command/flag names. Clear help messages.
- **NFR2 (Usability):** Error reporting distinguishes CLI/config, auth, plugin, and backend API errors. Stack traces (at high verbosity) indicate responsible module/component.
- **NFR3 (Performance):** Minimal CLI startup time. Command execution time reflects API latency and token acquisition if needed.
- **NFR4 (Reliability):** Graceful handling of network/API errors. Clear reporting of token refresh failures.
- **NFR5 (Security):** Secrets should be sourced from OS env vars or env-specific `.env` files. Users are responsible for securing these files. Storing secrets in main `.env` or CLI args discouraged. Tokens cached securely (user responsibility).
- **NFR6 (Maintainability):** Core and plugins as distinct Python packages. Core: 100% test coverage. Plugins: self-managed. Code style: PEP 8, type hints, tests for config loading, auth, and token logic.
- **NFR7 (Extensibility):** Plugin interface clearly documented for easy plugin development/distribution.
- **NFR8 (Compatibility):** Supported: Linux, macOS (x86_64, ARM64), Windows (via WSL2). Python 3.11+. Install via `uv`.

---

## 7. Design & Architecture

- **Core:** Python app using `click` (CLI), `pluggy` (plugins), `python-dotenv` (config), `logging` + `rich` (logging), `httpx` (HTTP). Handles orchestration, config precedence, auth (with caching/refresh), context, I/O, help, and versioning, and **input from STDIN via --file -**.
- **Plugins:** Separate Python packages using `pluggy` hooks to register `click` commands. Use provided context (including authenticated `httpx` client) for backend interaction. Plugins are encouraged to support `--file -` for STDIN input.
- *(See High-Level Architecture Overview for details)*

---

## 8. Release Criteria / Minimum Viable Product (MVP)

- Core `lmi` executable meeting all functional requirements (FR1, FR1.1, FR2, FR4, FR4.1, FR4.2, FR7–FR16, Plugin Lifecycle)
- Authentication: Demonstrate Client Credentials & Password grant auth, with token caching and refresh on 401
- Output/help/version: JSON output, help system, version reporting
- Plugin loading: Discover/load a test/example plugin (e.g., "hello" or "ping")
- Plugin lifecycle: Install, uninstall, and list plugins via CLI
- Documentation: README covering install, config, usage, plugin system, and security best practices
- Packaged/installable via `uv` (internal Git repo or PyPI)

---

## 9. Future Considerations
- Service plugins (e.g., `lmi-plugin-accsvc`, `lmi-plugin-clientmgr`, `lmi-plugin-oauthsvc`)
- Additional output formats (tables, plain text)
- Support for more OAuth flows (e.g., Auth Code + PKCE)
- Plugin lifecycle commands (already MVP)
- Shell autocompletion (bash, zsh, fish)
- Generic response caching for plugins
- Built-in workflow commands (e.g., `lmi workflow run create-standard-user`)
- Opt-in telemetry
- System keyring integration for secrets
- Project-local config files

---

## 10. Decisions on Open Technical Questions (May 2025)

1. **File Security & Permissions:**
   - Users are responsible for securing their own `.env` and token cache files. The CLI will not enforce or check file permissions. Users can review logs to see what configuration variables were used.
   - Dynamic reloading of configuration is not supported; configuration is loaded once at startup.
2. **Token Caching & Refresh:**
   - The CLI will not manage file permissions for token caches, nor is extensibility a current concern.
   - If token refresh fails, an error will be delivered to the user. Token expiry will be checked based on the expiry time included in the token (token details to be specified later).
3. **Configuration Sources:**
   - Any configuration value that can be set may be set via `.env` file, environment variable, or CLI argument, following the documented precedence.
4. **Plugin Security & Isolation:**
   - Plugins are not sandboxed. If a user installs a plugin, it can do anything it is able to do within the Python process.
5. **Output Formatting & Schemas:**
   - Each plugin command is responsible for its own output format. There is no enforced schema. Support for additional output formats is opt-in for plugins.
6. **Error Handling & Interactivity:**
   - The CLI will use a standard exception stack that denotes error domains (e.g., core, plugin, auth, backend). The CLI is strictly non-interactive; missing configuration or secrets will result in errors, not prompts.
7. **Keyring & Secret Management:**
   - No keyring or advanced secret management in the MVP. This will be considered in a future iteration.
8. **Testing & Plugin Quality:**
   - The core CLI will maintain 100% test coverage. Plugins are responsible for their own testing and quality. The core will provide a mechanism to install published plugins (primarily from internal repositories, configurable via a command). The core is only responsible for providing a consistent set of globals and hookpoints for plugins.
9. **Platform Support:**
   - The CLI will support Linux, macOS, and WSL. Native Windows (cmd/PowerShell) support is not in scope for the MVP.
10. **Installation & Distribution:**
    - The project will use `uv` for environment and dependency management, but will also support standard installation via `pip` or other Python tools. Plugins may be distributed via internal or external repositories as configured.
11. **Documentation:**
    - Plugin developer documentation and user security guidance are out of scope for the MVP and may be addressed in future iterations.

---

## 11. Remaining Open Questions

- [ ] Token details (structure, expiry field, etc.) to be specified for implementation.
- [ ] Are there any additional requirements for plugin discovery or installation workflows (e.g., plugin version pinning, trusted sources)?
- [ ] Should there be a mechanism for users to manually clear the token cache if needed?

---

*(End of Document)*
