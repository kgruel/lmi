"""Main entry point for the lmi CLI application."""

import logging
import sys
from typing import Optional

import click

from lmi.auth import AuthenticatedClient
from lmi.cli.auth import auth as auth_group
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
    @click.option(
        "-C",
        "--config-override",
        "cli_config_overrides",
        multiple=True,
        type=str,
        help="Override a configuration key (e.g., -C OAUTH_TOKEN_URL=http://...)",
    )
    @click.pass_context
    def cli(ctx, environment: str | None, verbose: int, no_file_log: bool, output: str, cli_config_overrides: tuple[str, ...]) -> None:
        """lmi: Unified Platform CLI.

        Args:
            environment: Optional environment name to load configuration from.
            verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
            no_file_log: Disable file logging
            output: Output format (json, ...)
            cli_config_overrides: List of KEY=VALUE pairs to override configuration

        """
        setup_logging(verbosity=verbose, disable_file=no_file_log)
        logging.getLogger(__name__).info("lmi CLI starting up")
        # Store global options in context for later use
        ctx.ensure_object(dict)
        ctx.obj["environment"] = environment
        ctx.obj["verbose"] = verbose
        ctx.obj["no_file_log"] = no_file_log
        ctx.obj["output"] = output
        
        # Parse config overrides
        parsed_overrides = {}
        for override in cli_config_overrides:
            if '=' not in override:
                raise click.BadParameter(f"Config overrides must be in KEY=VALUE format: {override}")
            key, value = override.split('=', 1)
            parsed_overrides[key] = value
        ctx.obj["config_overrides"] = parsed_overrides

    # Add auth commands
    cli.add_command(auth_group)

    @cli.result_callback()
    @click.pass_context
    def process_result(ctx, *args, **kwargs):
        # Only run if a subcommand was actually invoked (not for --help/--version)
        if ctx.invoked_subcommand is None:
            return
        environment = ctx.obj.get("environment")
        verbose = ctx.obj.get("verbose")
        no_file_log = ctx.obj.get("no_file_log")
        output = ctx.obj.get("output")
        config_overrides = ctx.obj.get("config_overrides", {})
        try:
            config = load_config(environment=environment, cli_args=config_overrides)
            logging.getLogger(__name__).info("Configuration loaded successfully")
            logger = logging.getLogger("lmi.plugins")
            client = AuthenticatedClient(config, environment or config.get("default_environment"))
            global_flags = {"environment": environment, "verbose": verbose, "no_file_log": no_file_log, "output": output}
            context = CliContext(config, logger, client, global_flags)
            # Register plugins
            plugin_manager.register_plugins(ctx.command, context)
        except RuntimeError as e:
            logging.getLogger(__name__).error(f"Config error: {e}")
            click.echo(f"Config error: {e}", err=True)
            raise click.Abort() from e

    @cli.group()
    def plugin():
        """Manage lmi plugins (install, uninstall, list)."""

    @plugin.command()
    @click.argument("package")
    @click.option("--index-url", help="Custom package index URL (optional)")
    def install(package, index_url):
        """Install a plugin from PyPI or a custom index."""
        import subprocess
        cmd = ["uv", "pip", "install", package]
        if index_url:
            cmd += ["--index-url", index_url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            click.echo(f"Plugin '{package}' installed successfully.")
        else:
            click.echo(result.stderr, err=True)
            raise click.ClickException(f"Failed to install plugin '{package}'")

    @plugin.command()
    @click.argument("package")
    def uninstall(package):
        """Uninstall a plugin by package name."""
        import subprocess
        cmd = ["uv", "pip", "uninstall", "-y", package]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            click.echo(f"Plugin '{package}' uninstalled successfully.")
        else:
            click.echo(result.stderr, err=True)
            raise click.ClickException(f"Failed to uninstall plugin '{package}'")

    @plugin.command()
    def list():
        """List installed lmi plugins and their versions."""
        import importlib.metadata
        plugins = importlib.metadata.entry_points().get("lmi_plugins", [])
        if not plugins:
            click.echo("No plugins installed.")
            return
        data = [
            {"name": ep.name, "module": ep.value, "version": importlib.metadata.version(ep.dist.name)}
            for ep in plugins
        ]
        format_output(data, output_format="json")

    return cli

# Output formatting utility
import json as _json


def format_output(data, output_format: str = "json"):
    if output_format == "json":
        click.echo(_json.dumps(data, indent=2, ensure_ascii=False))
    else:
        click.echo(str(data))

def read_input_file(file: Optional[str]) -> str:
    """
    Read input data from a file or STDIN.
    If file is '-', read from sys.stdin.
    Returns the input as a string.
    Raises click.ClickException on error or empty input.
    """
    if file is None:
        raise click.ClickException("No input file specified.")
    if file == "-":
        data = sys.stdin.read()
        if not data.strip():
            raise click.ClickException("STDIN is empty. Provide input data or use --file <path>.")
        return data
    try:
        with open(file, encoding="utf-8") as f:
            data = f.read()
            if not data.strip():
                raise click.ClickException(f"Input file '{file}' is empty.")
            return data
    except FileNotFoundError:
        raise click.ClickException(f"Input file not found: {file}")
    except Exception as e:
        raise click.ClickException(f"Failed to read input file '{file}': {e}")

cli = create_cli()

if __name__ == "__main__":
    cli()
