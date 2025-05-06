"""Tests for the lmi CLI entry point."""

import subprocess
import sys


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
