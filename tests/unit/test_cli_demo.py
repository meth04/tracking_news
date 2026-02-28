"""Unit tests cho lệnh demo CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner

from news_ingestor.cli import cli


def test_demo_missing_dashboard(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(Path, "exists", lambda _self: False)

    result = runner.invoke(cli, ["demo"])

    assert result.exit_code != 0
    assert "Không tìm thấy dashboard.py" in result.output


def test_demo_missing_streamlit(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(Path, "exists", lambda _self: True)
    monkeypatch.setattr("news_ingestor.cli.importlib.util.find_spec", lambda _name: None)

    result = runner.invoke(cli, ["demo"])

    assert result.exit_code != 0
    assert "Thiếu dependency 'streamlit'" in result.output


def test_demo_success(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(Path, "exists", lambda _self: True)
    monkeypatch.setattr("news_ingestor.cli.importlib.util.find_spec", lambda _name: object())
    monkeypatch.setattr("news_ingestor.cli._tim_cong_trong", lambda: 18765)

    proc = Mock()
    proc.returncode = 0
    run_mock = Mock(return_value=proc)
    monkeypatch.setattr("news_ingestor.cli.subprocess.run", run_mock)

    result = runner.invoke(cli, ["demo"])

    assert result.exit_code == 0
    assert "http://127.0.0.1:18765" in result.output
    assert run_mock.called
