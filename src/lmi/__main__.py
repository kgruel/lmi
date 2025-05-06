"""Main entry point for the lmi CLI application."""

import logging

import click

from lmi.config import load_config
from lmi.logging import setup_logging


@click.group()
@click.version_option("0.1.0", message="%(version)s")
@click.option(
    "-e",
    "--environment",
    help="Select environment (from ~/.config/lmi/env/<env>.env)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v=INFO, -vv=DEBUG)",
)
@click.option(
    "--no-file-log",
    is_flag=True,
    default=False,
    help="Disable file logging",
)
def cli(environment: str | None, verbose: int, no_file_log: bool) -> None:
    """lmi: Unified Platform CLI.

    Args:
        environment: Optional environment name to load configuration from.
        verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
        no_file_log: Disable file logging

    """
    setup_logging(verbosity=verbose, disable_file=no_file_log)
    logging.getLogger(__name__).info("lmi CLI starting up")
    try:
        load_config(environment=environment)
        logging.getLogger(__name__).info("Configuration loaded successfully")
        # Store config in context or pass to commands as needed
    except RuntimeError as e:
        logging.getLogger(__name__).error(f"Config error: {e}")
        click.echo(f"Config error: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    cli()
