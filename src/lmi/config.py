"""Configuration loading utilities for the lmi CLI application."""

import os
from pathlib import Path

from dotenv import dotenv_values

CONFIG_DIR = Path.home() / ".config" / "lmi"
ENV_DIR = CONFIG_DIR / "env"
MAIN_ENV_FILE = CONFIG_DIR / ".env"

REQUIRED_CONFIG_KEYS: list[str] = []
OAUTH_REQUIRED_KEYS = [
    "OAUTH_CLIENT_ID",
    "OAUTH_CLIENT_SECRET",
    "OAUTH_TOKEN_URL",
    # Add more as needed for Password Grant
]

# SSO-specific configuration keys
SSO_REQUIRED_KEYS = [
    "OAUTH_SSO_CLIENT_ID",
    "OAUTH_SSO_AUTHORIZATION_URL",
    "OAUTH_SSO_TOKEN_URL",
]

def load_config(
    cli_args: dict[str, str] | None = None,
    environment: str | None = None,
    require_oauth: bool = False,
    require_sso: bool = False,
) -> dict[str, str]:
    """Load configuration with precedence.

    1. CLI args
    2. OS environment variables
    3. Env-specific .env file
    4. Main .env file
    5. Built-in defaults (not implemented)

    Args:
        cli_args: Optional dictionary of CLI arguments.
        environment: Optional environment name.
        require_oauth: Whether to require OAuth keys.
        require_sso: Whether to require SSO keys.

    Returns:
        dict[str, str]: Loaded configuration.

    """
    config: dict[str, str] = {}

    # 4. Main .env file
    if MAIN_ENV_FILE.exists():
        config.update(dotenv_values(str(MAIN_ENV_FILE)))

    # 2. Determine environment
    env_name = environment or config.get("default_environment")
    if not env_name:
        msg = "No environment specified and no default_environment in main .env"
        raise RuntimeError(msg)
    env_file = ENV_DIR / f"{env_name}.env"
    if env_file.exists():
        config.update(dotenv_values(str(env_file)))
    else:
        msg = f"Environment file not found: {env_file}"
        raise RuntimeError(msg)

    # 2. OS environment variables
    config.update({k: v for k, v in os.environ.items() if v is not None})

    # 1. CLI args
    if cli_args:
        config.update({k: v for k, v in cli_args.items() if v is not None})

    # Check required keys
    required_keys = REQUIRED_CONFIG_KEYS.copy()
    if require_oauth:
        required_keys += OAUTH_REQUIRED_KEYS
    if require_sso:
        required_keys += SSO_REQUIRED_KEYS
    missing = [k for k in required_keys if k not in config or not config[k]]
    if missing:
        msg = f"Missing required config: {', '.join(missing)}"
        raise RuntimeError(msg)

    return config
