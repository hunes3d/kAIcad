"""CLI smoke tests to ensure entrypoints are wired and parse --help without side effects."""

import subprocess
import sys


def run_cmd(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_cli_main_help():
    cp = run_cmd([sys.executable, "-m", "sidecar.main", "-h"])
    assert cp.returncode == 0
    assert "kAIcad CLI" in cp.stdout


def test_cli_web_help():
    cp = run_cmd([sys.executable, "-m", "sidecar.web", "-h"])
    assert cp.returncode == 0
    assert "kAIcad Web GUI" in cp.stdout
