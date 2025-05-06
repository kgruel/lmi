# Error Handling

Learn how **lmi** reports errors, how to troubleshoot common issues, and how to get more information using verbosity flags.

## 1. Types of Errors

- **Configuration errors:** Missing or invalid config values, file not found, etc.
- **Authentication errors:** Invalid credentials, token expired, token refresh failed.
- **Plugin errors:** Issues in plugin code or command execution.
- **Backend API errors:** Errors returned from remote services.

## 2. Troubleshooting Steps

- Read the error message for details on what went wrong.
- For config errors, check your `.env` files and environment variables.
- For authentication errors, verify your client ID, secret, and service URL.
- For plugin errors, ensure the plugin is installed and up to date.
- For backend errors, check network connectivity and service status.

## 3. Verbosity and Stack Traces

- Use `-v` for more detailed error messages (INFO level).
- Use `-vv` for full stack traces and debug output (DEBUG level).
- Stack traces will indicate the responsible module or component.

## 4. Getting More Help

- Use `lmi --help` or `lmi <command> --help` for usage info.
- Check the log file (`~/.local/share/lmi/lmi.log`) for more details.
- If you encounter a persistent issue, consult the FAQ or open an issue with logs and error details. 