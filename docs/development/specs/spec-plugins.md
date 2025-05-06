# lmi CLI Specification: Plugin System

## Scope and Rationale

This specification defines the plugin architecture for the `lmi` CLI, including plugin discovery, loading, lifecycle management, and extension interfaces. The goal is to enable extensibility, allowing new service-specific commands to be integrated seamlessly while maintaining security and consistency.

## Detailed Requirements and Design

### 1. Plugin Discovery and Loading
- Use `pluggy` for plugin management.
- Discover plugins via Python entry points (e.g., `lmi_plugins`).
- Plugins must be separate Python packages, installable via standard Python tooling (`uv`, `pip`).
- The CLI must support loading plugins from both internal and external repositories, as configured.

### 2. Plugin Registration
- Plugins register their `click` command groups via a `pluggy` hook (`register_commands`).
- Each plugin command group is integrated into the main CLI command tree.
- Plugins receive a `CliContext` object (resolved config, logger, authenticated HTTP client, global flags).

### 3. Plugin Lifecycle Management
- The CLI must provide commands to install, uninstall, and list plugins.
- Plugin installation supports both internal and external repositories.
- Uninstalling a plugin removes its commands from the CLI.
- Listing plugins shows installed plugins and their versions.

### 4. Security and Isolation
- Plugins are not sandboxed; they run in the same process as the core CLI.
- Users are responsible for reviewing and trusting plugins before installation.
- The CLI does not enforce plugin isolation or restrict plugin capabilities.

### 5. Output and Help Integration
- Plugins must support the `--help` flag for their commands, using `click`'s help system.
- Plugins may support additional output formats (e.g., tables, plain text) but must support JSON output by default.
- Plugins are responsible for their own output schemas and formatting.

### 6. Versioning and Compatibility
- The CLI must report both core and loaded plugin versions via `--version`.
- Plugins should declare their compatible `lmi` core version in their metadata.

## Implementation Guidelines
- Follow PEP 8 and use type hints.
- Document the plugin interface and lifecycle for developers.
- Provide example/test plugins for development and validation.
- Ensure plugin commands are discoverable via `lmi --help`.
- Plugins should be self-contained and manage their own dependencies.

## References to PRD Sections
- Functional Requirements: FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, Plugin Lifecycle
- Non-Functional Requirements: NFR6, NFR7, NFR8
- Design & Architecture
- Release Criteria / MVP
- Decisions on Open Technical Questions: Plugin Security & Isolation, Plugin Quality, Installation & Distribution

## Explicit Non-Requirements and Philosophy

- **No Version Pinning:** The core CLI does not enforce plugin version pinning or compatibility checks. Plugins are responsible for their own compatibility.
- **No Plugin Manifest:** Plugins do not require a manifest or metadata schema beyond what is needed for Python packaging and pluggy registration.
- **No Trust/Approval Process:** There is no formal process for plugin approval or trust. Users are responsible for reviewing and installing plugins at their own risk.
- **Dependency Management:** Plugin dependencies are managed by the Python package manager (e.g., pip, uv). The core CLI does not isolate or manage plugin dependencies.
- **Bring Your Own Risk:** The plugin system is intentionally open; users are responsible for the plugins they install and use. 