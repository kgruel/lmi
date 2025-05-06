# Logging & Output

Understand how **lmi** handles logging and output formatting, including log file locations, verbosity settings, and output formats.

## 1. Log File Locations

- **Default log file:**
  - Linux/macOS: `~/.local/share/lmi/lmi.log`
  - Windows (via WSL2): `%LOCALAPPDATA%\lmi\lmi.log`
- You can configure or disable file logging via CLI or config files.

## 2. Console Logging

- Console logs are sent to STDERR using rich formatting (`rich.logging.RichHandler`).
- Control verbosity with:
  - `-v` for INFO level
  - `-vv` for DEBUG level
- You can disable or further configure console logging in your config.

## 3. Output Formats

- Use `--output <format>` to control output formatting (default: JSON).
- Output is sent to STDOUT for easy scripting and automation.
- Plugins may support additional formats (e.g., tables, plain text), but JSON is always available.

## 4. Troubleshooting Logging & Output

- If you don't see expected logs, check your config for log file paths and verbosity settings.
- For more details, increase verbosity with `-v` or `-vv`.
- If your output is not in the expected format, check the `--output` flag and plugin documentation. 