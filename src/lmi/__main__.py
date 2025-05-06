import os
from typing import Dict, Optional
from dotenv import dotenv_values
import click

CONFIG_DIR = os.path.expanduser("~/.config/lmi")
ENV_DIR = os.path.join(CONFIG_DIR, "env")
MAIN_ENV_FILE = os.path.join(CONFIG_DIR, ".env")

REQUIRED_CONFIG_KEYS = [
    # Add required config keys here, e.g. 'OAUTH_CLIENT_ID', 'OAUTH_CLIENT_SECRET', etc.
]

def load_config(cli_args: Optional[Dict[str, str]] = None, environment: Optional[str] = None) -> Dict[str, str]:
    """
    Load configuration with precedence:
    1. CLI args
    2. OS environment variables
    3. Env-specific .env file
    4. Main .env file
    5. Built-in defaults (not implemented)
    """
    config = {}

    # 4. Main .env file
    if os.path.exists(MAIN_ENV_FILE):
        config.update(dotenv_values(MAIN_ENV_FILE))

    # 2. Determine environment
    env_name = environment or config.get("default_environment")
    if not env_name:
        raise RuntimeError("No environment specified and no default_environment in main .env")
    env_file = os.path.join(ENV_DIR, f"{env_name}.env")
    if os.path.exists(env_file):
        config.update(dotenv_values(env_file))
    else:
        raise RuntimeError(f"Environment file not found: {env_file}")

    # 2. OS environment variables
    config.update({k: v for k, v in os.environ.items() if v is not None})

    # 1. CLI args
    if cli_args:
        config.update({k: v for k, v in cli_args.items() if v is not None})

    # Check required keys
    missing = [k for k in REQUIRED_CONFIG_KEYS if k not in config or not config[k]]
    if missing:
        raise RuntimeError(f"Missing required config: {', '.join(missing)}")

    return config

@click.group()
@click.version_option("0.1.0", message="%(version)s")
@click.option("-e", "--environment", help="Select environment (from ~/.config/lmi/env/<env>.env)")
def cli(environment):
    """lmi: Unified Platform CLI"""
    try:
        load_config(environment=environment)
        # Store config in context or pass to commands as needed
    except Exception as e:
        click.echo(f"Config error: {e}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli() 