import sys
import subprocess

def test_cli_version():
    result = subprocess.run([
        sys.executable, "main.py", "--version"
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert "0.1.0" in result.stdout or "0.1.0" in result.stderr 