# Quickstart

Get started with **lmi** in minutes. This guide covers installation, basic configuration, and running your first command.

## 1. Installation

### Using [uv](https://github.com/astral-sh/uv) (recommended)
```sh
uv pip install lmi
```

### Using pip
```sh
pip install lmi
```

## 2. Initial Configuration

Create your main config file:
```sh
mkdir -p ~/.config/lmi/env
cat > ~/.config/lmi/.env <<EOF
# Main lmi config
# Set your default environment name
DEFAULT_ENVIRONMENT=dev
EOF
```

Create an environment-specific config file (example: `dev.env`):
```sh
cat > ~/.config/lmi/env/dev.env <<EOF
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_SERVICE_URL=https://auth.example.com
EOF
```

> **Tip:** Secrets should be stored in environment variables or env-specific `.env` files, not in the main `.env`.

## 3. Running Your First Command

Check your installation and see available commands:
```sh
lmi --help
```

Run a command using your environment:
```sh
lmi -e dev <service_group> <action> [options]
```

Example (replace with a real command when available):
```sh
lmi -e dev ping
```

## 4. Switching Environments

Add more `.env` files in `~/.config/lmi/env/` and use `-e <env_name>` to switch.

## 5. Troubleshooting
- Use `-v` or `-vv` for more verbose output.
- Check `~/.local/share/lmi/lmi.log` for logs.
- For config errors, ensure your `.env` files are in the correct location and have the required values. 