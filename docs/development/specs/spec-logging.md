# lmi CLI Specification: Logging, Error Handling, and Output Formatting

## Scope and Rationale

This specification covers the logging system, error handling strategy, and output formatting for the `lmi` CLI. The goal is to ensure clear, actionable feedback for users and maintainers, support troubleshooting, and provide consistent, scriptable output for automation.

## Detailed Requirements and Design

### 1. Logging
- File logs:
  - Default location: `~/.local/share/lmi/lmi.log` (Linux/macOS) or `%LOCALAPPDATA%\lmi\lmi.log` (Windows via WSL2).
  - Logging can be disabled or configured via CLI or config.
- Console logs:
  - Output to STDERR using `rich.logging.RichHandler` for enhanced formatting.
  - Verbosity controlled by `-v` (INFO), `-vv` (DEBUG). Can be disabled/configured.
- Log messages must distinguish between core, plugin, authentication, and backend API events.
- Logs should include timestamps, log level, and source module/component.

### 2. Error Handling
- Error reporting must distinguish between CLI/config errors, authentication errors, plugin errors, and backend API errors.
- At high verbosity, stack traces must indicate the responsible module/component.
- The CLI is strictly non-interactive: missing configuration or secrets result in errors, not prompts.
- Graceful handling of network/API errors, with clear reporting of token refresh failures.

### 3. Output Formatting
- Output formatting controlled by `--output <format>` (default: JSON).
- Output is sent to STDOUT for easy scripting and automation.
- Plugins may support additional formats (e.g., tables, plain text), but JSON is required.
- Each plugin is responsible for its own output schema and formatting.

### 4. Help and Version Reporting
- Context-aware help via `--help` at all CLI levels, using `click`.
- Version reporting via `--version` (core and loaded plugin versions).

## Implementation Guidelines
- Use Python's `logging` module with `rich` for console output.
- Ensure log file and console output are consistent and configurable.
- Provide clear, actionable error messages at all verbosity levels.
- Follow PEP 8 and use type hints.
- Test logging and error handling for all major error domains.

## References to PRD Sections
- Functional Requirements: FR7, FR12, FR13, FR14
- Non-Functional Requirements: NFR1, NFR2, NFR3, NFR4
- Design & Architecture
- Release Criteria / MVP
- Decisions on Open Technical Questions: Error Handling & Interactivity, Output Formatting & Schemas

## Explicit Non-Requirements and Philosophy

- **No Log Rotation/Retention:** The CLI does not implement log rotation or retention policies. Log files will grow until manually managed by the user.
- **No Minimum Output Schema:** Plugins are only required to support JSON output, but the structure and schema of their output is up to the plugin author.
- **Sensitive Value Handling:** Handling of sensitive values in logs is addressed in the core configuration manager specification. 