# Roadmap

See what's planned for future releases of **lmi**, including upcoming features and known limitations.

## Planned Features
- Service plugins (e.g., `lmi-plugin-accsvc`, `lmi-plugin-clientmgr`, `lmi-plugin-oauthsvc`)
- Additional output formats (tables, plain text)
- Support for more OAuth flows (e.g., Auth Code + PKCE)
- Shell autocompletion (bash, zsh, fish)
- Generic response caching for plugins
- Built-in workflow commands (e.g., `lmi workflow run create-standard-user`)
- Opt-in telemetry
- System keyring integration for secrets
- Project-local config files

## Known Limitations
- No GUI or web UI
- No built-in workflow engine (users script via shell/other tools)
- No direct database/backend storage interaction
- No real-time monitoring or dashboards
- No plugin sandboxing (plugins run in the same process)
- No log rotation or retention policy
- No keyring or advanced secret management in MVP
- Native Windows (cmd/PowerShell) support is not in scope for MVP (use WSL2) 