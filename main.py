import click

@click.group()
@click.version_option("0.1.0", message="%(version)s")
def cli():
    """lmi: Unified Platform CLI"""
    pass

if __name__ == "__main__":
    cli()
