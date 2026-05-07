from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mimocast.cli import app

runner = CliRunner()


def test_version() -> None:
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "mimocast" in res.stdout


def test_run_mock_dry_run(monkeypatch, tmp_path: Path, sample_markdown: Path) -> None:
    monkeypatch.setenv("MIMOCAST_API_KEY", "")
    monkeypatch.setenv("MIMOCAST_WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setenv("MIMOCAST_OUT_DIR", str(tmp_path / "out"))

    res = runner.invoke(
        app,
        ["run", str(sample_markdown), "--mock", "--dry-run", "--max-sections", "3"],
    )
    assert res.exit_code == 0, res.stdout
    # Pipeline persisted at least one run state file in the work dir
    state_files = list((tmp_path / "work").glob("*.json"))
    assert state_files, "expected at least one persisted run state"


def test_list_runs_empty(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MIMOCAST_WORK_DIR", str(tmp_path / "work"))
    res = runner.invoke(app, ["list"])
    assert res.exit_code == 0
