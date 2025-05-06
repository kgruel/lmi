"""Tests for the lmi CLI entry point."""

import subprocess
import sys
import json
import click
from click.testing import CliRunner
from lmi.__main__ import cli, format_output


def test_cli_version() -> None:
    """Test that the CLI version command returns the correct version string."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lmi",
            "--version",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout or "0.1.0" in result.stderr

def test_cli_output_json(monkeypatch, tmp_path):
    """Test that the CLI outputs valid JSON for a dummy command with --output json."""
    # Setup temp config dirs/files
    config_dir = tmp_path / ".config" / "lmi"
    env_dir = config_dir / "env"
    env_dir.mkdir(parents=True)
    main_env = config_dir / ".env"
    env_file = env_dir / "testenv.env"
    main_env.write_text("default_environment=testenv\n")
    env_file.write_text("")
    monkeypatch.setattr("lmi.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("lmi.config.ENV_DIR", env_dir)
    monkeypatch.setattr("lmi.config.MAIN_ENV_FILE", main_env)
    # Patch AuthenticatedClient to a dummy in both lmi.auth and lmi.__main__
    import lmi.auth
    import lmi.__main__ as lmi_main
    class DummyClient:
        def __init__(self, *a, **k): pass
    monkeypatch.setattr(lmi.auth, "AuthenticatedClient", DummyClient)
    monkeypatch.setattr(lmi_main, "AuthenticatedClient", DummyClient)

    @cli.command()
    @click.pass_context
    def dummy(ctx):
        format_output({"foo": "bar"}, ctx.parent.params.get("output", "json"))

    runner = CliRunner()
    result = runner.invoke(cli, ["--output", "json", "dummy"])
    print("STDOUT:", result.output)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == {"foo": "bar"}

def test_cli_help():
    """Test that the CLI --help output is present and includes output option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "Output format" in result.output
