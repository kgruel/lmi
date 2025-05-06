# Plugin System

Learn how to extend **lmi** with plugins, manage plugin lifecycle, and develop your own plugins.

## 1. How Plugins Work

- Plugins are separate Python packages that add new commands to lmi.
- lmi discovers plugins using Python entry points (via `pluggy`).
- Plugins are loaded at startup and integrated into the CLI command tree.

## 2. Installing, Uninstalling, and Listing Plugins

- **Install a plugin:**
  ```sh
  lmi plugin install <plugin-package>
  ```
- **Uninstall a plugin:**
  ```sh
  lmi plugin uninstall <plugin-package>
  ```
- **List installed plugins:**
  ```sh
  lmi plugin list
  ```
- Plugins can be installed from internal or external repositories (as configured).

## 3. Example Plugin Usage

After installing a plugin, its commands become available:
```sh
lmi <plugin-command-group> <action> [options]
```
Use `lmi --help` to see all available commands, including those from plugins.

## 4. Developing Plugins (Overview)

- Create a new Python package and declare an entry point for `lmi_plugins`.
- Register your command group using the `register_commands` pluggy hook.
- Use the provided `CliContext` for config, logging, and authenticated HTTP client.
- Follow PEP 8, use type hints, and provide help text for your commands.

> See the development guide and example plugins for more details. 