# Configuration

Learn how to configure **lmi** using `.env` files, environment variables, and CLI arguments. This section explains configuration precedence, file locations, and provides sample config files.

## 1. Configuration Sources & Precedence

lmi supports multiple configuration sources, applied in the following order (highest to lowest precedence):

1. **Command-line arguments** (e.g., `--oauth_service_url ...`)
2. **OS environment variables** (e.g., `export OAUTH_CLIENT_SECRET=...`)
3. **Environment-specific `.env` file** (e.g., `~/.config/lmi/env/dev.env`)
4. **Main `.env` config file** (`~/.config/lmi/.env`)
5. **Built-in defaults** (if any)

> The first source that provides a value for a config key is used.

## 2. Config File Locations

- **Main config:** `~/.config/lmi/.env` (optional)
- **Environment configs:** `~/.config/lmi/env/<env_name>.env` (one per environment)

## 3. Example Config Files

**Main `.env` file:**
```ini
# ~/.config/lmi/.env
DEFAULT_ENVIRONMENT=dev
LOG_FILE=~/.local/share/lmi/lmi.log
```

**Environment-specific `.env` file:**
```ini
# ~/.config/lmi/env/dev.env
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_SERVICE_URL=https://auth.example.com
```

## 4. Selecting and Switching Environments

- Use `-e <env_name>` or `--environment <env_name>` to select an environment.
- If not specified, lmi uses the `DEFAULT_ENVIRONMENT` from the main `.env`.
- If neither is set, lmi will error and prompt you to specify an environment.

## 5. Overriding Config Values

- Any config value can be overridden at the command line or via environment variables.
- Example:
  ```sh
  OAUTH_CLIENT_SECRET=override-secret lmi -e dev ...
  lmi -e dev --oauth_service_url https://override.example.com ...
  ```

## 6. Security Best Practices

- **Store secrets** (client secrets, passwords) in environment variables or env-specific `.env` files.
- **Do not** store secrets in the main `.env` or pass them on the command line unless necessary.
- You are responsible for securing your `.env` and token cache files.

## 7. Troubleshooting

- Missing required config values will result in clear error messages.
- Check your file locations and variable names if you encounter config errors.
- Use `-v` or `-vv` for more detailed error output. 