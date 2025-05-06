"""Main entry point for the lmi CLI application."""

import click

from lmi.config import load_config


@click.group()
@click.version_option("0.1.0", message="%(version)s")
@click.option(
    "-e",
    "--environment",
    help="Select environment (from ~/.config/lmi/env/<env>.env)",
)
def cli(environment: str | None) -> None:
    """lmi: Unified Platform CLI.

    Args:
        environment: Optional environment name to load configuration from.

    """
    try:
        load_config(environment=environment)
        # Store config in context or pass to commands as needed
    except RuntimeError as e:
        click.echo(f"Config error: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    cli()
