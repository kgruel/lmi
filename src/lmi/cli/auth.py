"""CLI commands for authentication."""

import datetime
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from lmi.config import load_config
from lmi.sso import SSOAuth

console = Console()

@click.group()
def auth() -> None:
    """Authentication commands."""
    pass

@auth.command()
@click.option("--force", is_flag=True, help="Force re-authentication even if already logged in")
def login(force: bool) -> None:
    """Log in using SSO."""
    try:
        config = load_config(require_sso=True)
        sso = SSOAuth(config)

        if not force and sso.get_token():
            console.print("[yellow]Already logged in. Use --force to re-authenticate.[/yellow]")
            return

        token = sso.login()
        console.print("[green]Successfully logged in via SSO[/green]")
        if token.id_token:
            # TODO: Decode and display user info from ID token
            pass

    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        raise click.Abort()

@auth.command()
def logout() -> None:
    """Log out from SSO."""
    try:
        config = load_config(require_sso=True)
        sso = SSOAuth(config)
        sso.logout()
        console.print("[green]Successfully logged out[/green]")
    except Exception as e:
        console.print(f"[red]Logout failed: {e}[/red]")
        raise click.Abort()

@auth.command()
def status() -> None:
    """Show SSO login status."""
    try:
        config = load_config(require_sso=True)
        sso = SSOAuth(config)
        status = sso.get_status()

        if not status["logged_in"]:
            console.print("[yellow]Not logged in via SSO[/yellow]")
            return

        table = Table(title="SSO Login Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        # Add status information
        expires_at = datetime.datetime.fromtimestamp(status["expires_at"])
        table.add_row("Login Status", "Logged in")
        table.add_row("Expires At", expires_at.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Expires In", f"{status['expires_in'] // 60} minutes")
        table.add_row("Has Refresh Token", str(status["has_refresh_token"]))
        table.add_row("Has ID Token", str(status["has_id_token"]))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to get status: {e}[/red]")
        raise click.Abort() 