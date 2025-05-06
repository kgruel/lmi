"""Tests for the lmi CLI entry point."""

import json
import subprocess
import sys
import io
import tempfile
import os

import click
from click.testing import CliRunner
import pytest

from lmi.__main__ import cli, format_output, read_input_file


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
    import lmi.__main__ as lmi_main
    import lmi.auth
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

def setup_dummy_env(monkeypatch, tmp_path):
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

def patch_authenticated_client(monkeypatch):
    import lmi.__main__ as lmi_main
    import lmi.auth
    class DummyClient:
        def __init__(self, *a, **k): pass
    monkeypatch.setattr(lmi.auth, "AuthenticatedClient", DummyClient)
    monkeypatch.setattr(lmi_main, "AuthenticatedClient", DummyClient)

def test_plugin_install_success(monkeypatch, tmp_path):
    patch_authenticated_client(monkeypatch)
    setup_dummy_env(monkeypatch, tmp_path)
    runner = CliRunner()
    class Result:
        returncode = 0
        stderr = ""
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Result())
    result = runner.invoke(cli, ["plugin", "install", "some-plugin"])
    assert result.exit_code == 0
    assert "installed successfully" in result.output

def test_plugin_install_failure(monkeypatch, tmp_path):
    patch_authenticated_client(monkeypatch)
    setup_dummy_env(monkeypatch, tmp_path)
    runner = CliRunner()
    class Result:
        returncode = 1
        stderr = "Install failed"
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Result())
    result = runner.invoke(cli, ["plugin", "install", "bad-plugin"])
    assert result.exit_code != 0
    assert "Failed to install plugin" in result.output

def test_plugin_uninstall_success(monkeypatch, tmp_path):
    patch_authenticated_client(monkeypatch)
    setup_dummy_env(monkeypatch, tmp_path)
    runner = CliRunner()
    class Result:
        returncode = 0
        stderr = ""
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Result())
    result = runner.invoke(cli, ["plugin", "uninstall", "some-plugin"])
    assert result.exit_code == 0
    assert "uninstalled successfully" in result.output

def test_plugin_uninstall_failure(monkeypatch, tmp_path):
    patch_authenticated_client(monkeypatch)
    setup_dummy_env(monkeypatch, tmp_path)
    runner = CliRunner()
    class Result:
        returncode = 1
        stderr = "Uninstall failed"
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Result())
    result = runner.invoke(cli, ["plugin", "uninstall", "bad-plugin"])
    assert result.exit_code != 0
    assert "Failed to uninstall plugin" in result.output

def test_plugin_list(monkeypatch, tmp_path):
    patch_authenticated_client(monkeypatch)
    setup_dummy_env(monkeypatch, tmp_path)
    runner = CliRunner()
    class Ep:
        def __init__(self, name, value, dist_name):
            self.name = name
            self.value = value
            class Dist:
                name = dist_name
            self.dist = Dist()
    fake_eps = [Ep("foo", "foo.module:Plugin", "foo-pkg"), Ep("bar", "bar.module:Plugin", "bar-pkg")]
    def fake_entry_points():
        return {"lmi_plugins": fake_eps}
    def fake_version(name):
        return {"foo-pkg": "1.2.3", "bar-pkg": "0.9.8"}[name]
    monkeypatch.setattr("importlib.metadata.entry_points", fake_entry_points)
    monkeypatch.setattr("importlib.metadata.version", fake_version)
    result = runner.invoke(cli, ["plugin", "list"])
    assert result.exit_code == 0
    assert "foo" in result.output
    assert "bar" in result.output
    assert "1.2.3" in result.output

def test_plugin_list_empty(monkeypatch, tmp_path):
    patch_authenticated_client(monkeypatch)
    setup_dummy_env(monkeypatch, tmp_path)
    runner = CliRunner()
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: {"lmi_plugins": []})
    result = runner.invoke(cli, ["plugin", "list"])
    assert result.exit_code == 0
    assert "No plugins installed" in result.output

def test_cli_config_error(monkeypatch, tmp_path):
    """Test that a config error is handled and aborts CLI."""
    import lmi.__main__ as lmi_main
    runner = CliRunner()
    # Patch load_config to raise RuntimeError
    monkeypatch.setattr(lmi_main, "load_config", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail config")))
    # Add a dummy command to force config loading
    @lmi_main.cli.command()
    def dummy():
        pass
    result = runner.invoke(lmi_main.cli, ["dummy"])
    assert result.exit_code != 0
    assert "Config error" in result.output


def test_format_output_non_json(monkeypatch):
    """Test format_output with a non-json output format."""
    import lmi.__main__ as lmi_main
    class DummyEcho:
        def __init__(self): self.value = None
        def __call__(self, val): self.value = val
    dummy_echo = DummyEcho()
    monkeypatch.setattr("click.echo", dummy_echo)
    lmi_main.format_output({"foo": "bar"}, output_format="text")
    assert dummy_echo.value == str({"foo": "bar"})


def test_main_entry(monkeypatch):
    """Test __main__ entrypoint via subprocess."""
    import sys
    import subprocess
    result = subprocess.run([sys.executable, "-m", "lmi", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Unified Platform CLI" in result.stdout or result.stderr

def test_plugin_list_with_plugins(monkeypatch, tmp_path):
    patch_authenticated_client(monkeypatch)
    import lmi.__main__ as lmi_main
    setup_dummy_env(monkeypatch, tmp_path)
    runner = CliRunner()
    class Ep:
        def __init__(self, name, value, dist_name):
            self.name = name
            self.value = value
            class Dist:
                name = dist_name
            self.dist = Dist()
    fake_eps = [Ep("foo", "foo.module:Plugin", "foo-pkg")]
    def fake_entry_points():
        return {"lmi_plugins": fake_eps}
    def fake_version(name):
        return {"foo-pkg": "1.2.3"}[name]
    monkeypatch.setattr("importlib.metadata.entry_points", fake_entry_points)
    monkeypatch.setattr("importlib.metadata.version", fake_version)
    result = runner.invoke(lmi_main.cli, ["plugin", "list"])
    assert result.exit_code == 0
    assert "foo" in result.output
    assert "1.2.3" in result.output

def test_read_input_file_from_file(tmp_path):
    file_path = tmp_path / "input.txt"
    file_path.write_text("hello world\n")
    assert read_input_file(str(file_path)) == "hello world\n"

def test_read_input_file_from_file_empty(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")
    with pytest.raises(click.ClickException) as exc:
        read_input_file(str(file_path))
    assert "empty" in str(exc.value)

def test_read_input_file_file_not_found():
    with pytest.raises(click.ClickException) as exc:
        read_input_file("/nonexistent/file.txt")
    assert "not found" in str(exc.value)

def test_read_input_file_from_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("data from stdin\n"))
    assert read_input_file("-") == "data from stdin\n"

def test_read_input_file_from_stdin_empty(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("   \n"))
    with pytest.raises(click.ClickException) as exc:
        read_input_file("-")
    assert "STDIN is empty" in str(exc.value)

def test_read_input_file_none():
    with pytest.raises(click.ClickException) as exc:
        read_input_file(None)
    assert "No input file specified" in str(exc.value)
