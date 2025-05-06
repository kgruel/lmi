"""Tests for lmi.config configuration loading logic."""

import shutil
import tempfile
from pathlib import Path

import pytest

from lmi.config import load_config


def write_env_file(path: Path, content: str) -> None:
    """Write content to an environment file.

    Args:
        path: Path to the file.
        content: Content to write.

    """
    with path.open("w") as f:
        f.write(content)


def test_config_precedence(monkeypatch) -> None:
    """Test configuration precedence: CLI args > OS env > env file > main .env."""
    # Setup temp config dirs/files
    temp_dir = Path(tempfile.mkdtemp())
    config_dir = temp_dir / ".config" / "lmi"
    env_dir = config_dir / "env"
    env_dir.mkdir(parents=True)
    main_env = config_dir / ".env"
    env_file = env_dir / "testenv.env"

    # Write main .env
    write_env_file(main_env, "FOO=main\ndefault_environment=testenv\nBAR=mainbar\n")
    # Write env-specific .env
    write_env_file(env_file, "FOO=env\nBAZ=envbaz\n")

    # Patch config paths
    monkeypatch.setattr("lmi.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("lmi.config.ENV_DIR", env_dir)
    monkeypatch.setattr("lmi.config.MAIN_ENV_FILE", main_env)

    # No overrides
    config = load_config(environment="testenv")
    assert config["FOO"] == "env"
    assert config["BAR"] == "mainbar"
    assert config["BAZ"] == "envbaz"

    # OS env override
    monkeypatch.setenv("FOO", "osenv")
    config = load_config(environment="testenv")
    assert config["FOO"] == "osenv"

    # CLI arg override
    config = load_config(cli_args={"FOO": "cliarg"}, environment="testenv")
    assert config["FOO"] == "cliarg"

    shutil.rmtree(temp_dir)


def test_missing_required(monkeypatch) -> None:
    """Test that missing required config keys raises an error."""
    temp_dir = Path(tempfile.mkdtemp())
    config_dir = temp_dir / ".config" / "lmi"
    env_dir = config_dir / "env"
    env_dir.mkdir(parents=True)
    main_env = config_dir / ".env"
    env_file = env_dir / "testenv.env"
    write_env_file(main_env, "default_environment=testenv\n")
    write_env_file(env_file, "")
    monkeypatch.setattr("lmi.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("lmi.config.ENV_DIR", env_dir)
    monkeypatch.setattr("lmi.config.MAIN_ENV_FILE", main_env)
    monkeypatch.setattr("lmi.config.REQUIRED_CONFIG_KEYS", ["FOO", "BAR"])
    with pytest.raises(RuntimeError) as exc:
        load_config(environment="testenv")
    assert "Missing required config" in str(exc.value)
    shutil.rmtree(temp_dir)
