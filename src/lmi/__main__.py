import click
from lmi.config import load_config

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