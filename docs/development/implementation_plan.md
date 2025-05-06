## 10. Packaging and Distribution
- **Description:**
  - Package the CLI for distribution via `uv`, PyPI, or internal index.
  - Document install, config, usage, and plugin system.
- **Dependencies:** Steps 1–9
- **Acceptance Criteria:**
  - CLI can be installed and run as per PRD (Release Criteria / MVP)
  - Documentation is complete and accurate

---

## 11. Input from STDIN (`--file -`)
- **Description:**
  - Add support for input from STDIN to core CLI and plugin commands that accept input data (e.g., JSON, YAML, or text).
  - Implement a `--file <path>` option for relevant commands, where `--file -` reads from STDIN.
  - Ensure clear error messages if STDIN is empty or input is invalid.
  - Update documentation and help output to describe this feature.
- **Dependencies:** Steps 5–10 (requires CLI command structure and plugin system)
- **Acceptance Criteria:**
  - Commands that accept input data support `--file <path>` and `--file -` for STDIN.
  - Plugins are encouraged to follow the same convention.
  - Tests cover reading from files and STDIN, including error cases.
  - Documentation and CLI help updated.
- **Status:**
  - Completed: Utility function for --file/- input is implemented, tested, and ready for use in core and plugin commands. All tests and linter pass. 