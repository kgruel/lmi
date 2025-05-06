"""Main entry point for the lmi CLI application."""

import logging

import click

from lmi.auth import AuthenticatedClient
from lmi.config import load_config
from lmi.logging import setup_logging
from lmi.plugins import CliContext, plugin_manager

def create_cli():
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
    @click.option(
        "--output",
        type=click.Choice(["json"], case_sensitive=False),
        default="json",
        show_default=True,
        help="Output format (default: json). Output is sent to STDOUT for scripting. Plugins may support additional formats.",
    )
    def cli(environment: str | None, verbose: int, no_file_log: bool, output: str) -> None:
        """lmi: Unified Platform CLI.

        Args:
            environment: Optional environment name to load configuration from.
            verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
            no_file_log: Disable file logging
            output: Output format (json, ...)
        """
        setup_logging(verbosity=verbose, disable_file=no_file_log)
        logging.getLogger(__name__).info("lmi CLI starting up")
        try:
            config = load_config(environment=environment)
            logging.getLogger(__name__).info("Configuration loaded successfully")
            # Prepare context for plugins
            logger = logging.getLogger("lmi.plugins")
            client = AuthenticatedClient(config, environment or config.get("default_environment"))
            global_flags = {"environment": environment, "verbose": verbose, "no_file_log": no_file_log, "output": output}
            context = CliContext(config, logger, client, global_flags)
            # Register plugins
            plugin_manager.register_plugins(cli, context)
        except RuntimeError as e:
            logging.getLogger(__name__).error(f"Config error: {e}")
            click.echo(f"Config error: {e}", err=True)
            raise click.Abort() from e
    return cli

# Output formatting utility
import json as _json

def format_output(data, output_format: str = "json"):
    if output_format == "json":
        click.echo(_json.dumps(data, indent=2, ensure_ascii=False))
    else:
        click.echo(str(data))

cli = create_cli()

if __name__ == "__main__":
    cli()
