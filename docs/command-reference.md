# Command Reference

Detailed reference for all **lmi** commands, global options, and usage examples.

## 1. Global Options

- `-e, --environment <env_name>`: Select the active environment
- `-v, -vv`: Increase verbosity (INFO, DEBUG)
- `--output <format>`: Output format (default: JSON)
- `--help`: Show help for any command or subcommand
- `--version`: Show version info for lmi and loaded plugins

## 2. Command Structure

```
lmi [global_options] <service_group|plugin> <action> [action_options]
```
- `service_group` is a core or plugin command group (e.g., `auth`, `plugin`, etc.)
- `action` is a specific command (e.g., `login`, `install`, etc.)

## 3. Example Commands

- Show help:
  ```sh
  lmi --help
  lmi plugin --help
  ```
- Run a command with a specific environment:
  ```sh
  lmi -e dev auth login
  ```
- List installed plugins:
  ```sh
  lmi plugin list
  ```
- Use a plugin command:
  ```sh
  lmi <plugin-group> <action> [options]
  ```

## 4. Getting Help

- Use `--help` at any level to see available commands and options:
  ```sh
  lmi --help
  lmi <service_group> --help
  lmi <service_group> <action> --help
  ```

- Plugin commands 