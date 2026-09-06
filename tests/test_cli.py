import os
import sys
import pytest
from typer.testing import CliRunner

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.cli import app

runner = CliRunner()


def test_cli_stats_command():
    """Verifies agent-eval stats CLI command output."""
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "Telemetry & Dataset Statistics" in result.output


def test_cli_run_command_success(tmp_path):
    """Verifies agent-eval run command on local code and test files."""
    code_file = tmp_path / "solution.py"
    test_file = tmp_path / "tests.py"

    code_file.write_text("def add(a, b):\n    return a + b\n")
    test_file.write_text("assert add(2, 3) == 5\nprint('PASSED')\n")

    result = runner.invoke(app, [
        "run",
        "--code-file", str(code_file),
        "--test-file", str(test_file),
        "--prompt", "Write an add function",
        "--language", "python",
        "--task-id", "CLI-TEST-001"
    ])

    assert result.exit_code == 0
    assert "Evaluation Metric Summary" in result.output


def test_cli_repo_command_success(tmp_path):
    """Verifies agent-eval repo command on local directory patch execution."""
    patch_file = tmp_path / "patch.py"
    patch_file.write_text("# Patch file content\n")

    result = runner.invoke(app, [
        "repo",
        "--repo", str(tmp_path),
        "--patch", str(patch_file),
        "--test-cmd", "python -c print('Repo_Pass')"
    ])

    assert result.exit_code == 0
    assert "Repo Sandbox Status" in result.output
