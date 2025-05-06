import os
import tempfile
import shutil
import pytest
from lmi.__main__ import load_config

def write_env_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def test_config_precedence(monkeypatch):
    # Setup temp config dirs/files
    temp_dir = tempfile.mkdtemp()
    config_dir = os.path.join(temp_dir, ".config", "lmi")
    env_dir = os.path.join(config_dir, "env")
    os.makedirs(env_dir)
    main_env = os.path.join(config_dir, ".env")
    env_file = os.path.join(env_dir, "testenv.env")

    # Write main .env
    write_env_file(main_env, "FOO=main\ndefault_environment=testenv\nBAR=mainbar\n")
    # Write env-specific .env
    write_env_file(env_file, "FOO=env\nBAZ=envbaz\n")

    # Patch config paths
    monkeypatch.setattr("lmi.__main__.CONFIG_DIR", config_dir)
    monkeypatch.setattr("lmi.__main__.ENV_DIR", env_dir)
    monkeypatch.setattr("lmi.__main__.MAIN_ENV_FILE", main_env)

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

def test_missing_required(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    config_dir = os.path.join(temp_dir, ".config", "lmi")
    env_dir = os.path.join(config_dir, "env")
    os.makedirs(env_dir)
    main_env = os.path.join(config_dir, ".env")
    env_file = os.path.join(env_dir, "testenv.env")
    write_env_file(main_env, "default_environment=testenv\n")
    write_env_file(env_file, "")
    monkeypatch.setattr("lmi.__main__.CONFIG_DIR", config_dir)
    monkeypatch.setattr("lmi.__main__.ENV_DIR", env_dir)
    monkeypatch.setattr("lmi.__main__.MAIN_ENV_FILE", main_env)
    monkeypatch.setattr("lmi.__main__.REQUIRED_CONFIG_KEYS", ["FOO", "BAR"])
    with pytest.raises(RuntimeError) as exc:
        load_config(environment="testenv")
    assert "Missing required config" in str(exc.value)
    shutil.rmtree(temp_dir) 