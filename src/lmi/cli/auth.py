"""CLI commands for authentication."""

import datetime
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from lmi.auth import AuthToken, get_token, save_token
from lmi.config import load_config

console = Console()

@click.group()
def auth() -> None:
    """Authentication commands."""
    pass

@auth.command()
@click.option("-e", "--environment", help="Environment to authenticate for")
@click.option("--force", is_flag=True, help="Force re-authentication even if already logged in")
def login(environment: str | None, force: bool) -> None:
    """Log in using the configured OAuth grant type."""
    try:
        config = load_config(environment=environment)
        env_name = environment or config.get("default_environment", "default")
        
        # Check if already logged in
        if not force and (token := get_token(config, env_name)):
            console.print("[yellow]Already logged in. Use --force to re-authenticate.[/yellow]")
            return
        
        # Get new token with interactive login allowed
        token = get_token(config, env_name, allow_interactive_for_new=True)
        if not token:
            console.print("[red]Login failed: Could not acquire token[/red]")
            raise click.Abort()
        
        console.print("[green]Successfully logged in[/green]")
        if token.id_token:
            # TODO: Decode and display user info from ID token
            pass

    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        raise click.Abort()

@auth.command()
@click.option("-e", "--environment", help="Environment to log out from")
def logout(environment: str | None) -> None:
    """Log out by clearing cached tokens."""
    try:
        config = load_config(environment=environment)
        env_name = environment or config.get("default_environment", "default")
        
        # Invalidate token by saving an empty one
        save_token(env_name, AuthToken(
            access_token="",
            refresh_token=None,
            id_token=None,
            expires_at=0
        ))
        console.print("[green]Successfully logged out[/green]")
    except Exception as e:
        console.print(f"[red]Logout failed: {e}[/red]")
        raise click.Abort()

@auth.command()
@click.option("-e", "--environment", help="Environment to check status for")
def status(environment: str | None) -> None:
    """Show authentication status."""
    try:
        config = load_config(environment=environment)
        env_name = environment or config.get("default_environment", "default")
        token = get_token(config, env_name)

        if not token:
            console.print("[yellow]Not logged in[/yellow]")
            return

        table = Table(title="Authentication Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        # Add status information
        expires_at = datetime.datetime.fromtimestamp(token.expires_at)
        table.add_row("Login Status", "Logged in")
        table.add_row("Grant Type", config.get("OAUTH_GRANT_TYPE", "client_credentials"))
        table.add_row("Expires At", expires_at.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Expires In", f"{max(0, token.expires_at - int(datetime.datetime.now().timestamp())) // 60} minutes")
        table.add_row("Has Refresh Token", str(bool(token.refresh_token)))
        table.add_row("Has ID Token", str(bool(token.id_token)))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to get status: {e}[/red]")
        raise click.Abort() 