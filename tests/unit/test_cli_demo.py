"""Unit tests cho lệnh demo CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner

from news_ingestor.cli import cli
from news_ingestor.utils.evaluation import BaoCaoDanhGiaPipeline


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


def test_evaluate_json(monkeypatch):
    runner = CliRunner()

    bao_cao = BaoCaoDanhGiaPipeline(
        generated_at="2026-02-28T00:00:00+00:00",
        window_days=7,
        total_articles=10,
        unique_sources=3,
        coverage={
            "has_content_ratio": 0.9,
            "has_summary_ratio": 0.8,
            "has_sentiment_ratio": 0.7,
            "has_tickers_ratio": 0.6,
            "has_vector_ratio": 0.5,
        },
        sentiment_distribution={"POSITIVE": 4, "NEGATIVE": 2, "NEUTRAL": 4},
        sentiment_average=0.1234,
        impact_distribution={"LOW": 5, "MEDIUM": 3, "HIGH": 2},
        high_impact_ratio=0.2,
        avg_original_length=500.0,
        avg_summary_length=120.0,
    )

    db_mock = Mock()
    db_mock.khoi_tao_bang.return_value = None

    repo_mock = Mock()
    repo_mock.lay_tat_ca.return_value = []

    monkeypatch.setattr("news_ingestor.storage.database.lay_quan_ly_db", lambda: db_mock)
    monkeypatch.setattr("news_ingestor.storage.repository.KhoTinTuc", lambda: repo_mock)
    monkeypatch.setattr(
        "news_ingestor.utils.evaluation.tao_bao_cao_pipeline",
        lambda ds_bai, so_ngay: bao_cao,
    )

    result = runner.invoke(cli, ["evaluate", "--json-output"])

    assert result.exit_code == 0
    assert '"total_articles": 10' in result.output


def test_evaluate_text(monkeypatch):
    runner = CliRunner()

    db_mock = Mock()
    db_mock.khoi_tao_bang.return_value = None

    repo_mock = Mock()
    repo_mock.lay_tat_ca.return_value = []

    bao_cao = BaoCaoDanhGiaPipeline(
        generated_at="2026-02-28T00:00:00+00:00",
        window_days=7,
        total_articles=0,
        unique_sources=0,
        coverage={
            "has_content_ratio": 0.0,
            "has_summary_ratio": 0.0,
            "has_sentiment_ratio": 0.0,
            "has_tickers_ratio": 0.0,
            "has_vector_ratio": 0.0,
        },
        sentiment_distribution={"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0},
        sentiment_average=0.0,
        impact_distribution={"LOW": 0, "MEDIUM": 0, "HIGH": 0},
        high_impact_ratio=0.0,
        avg_original_length=0.0,
        avg_summary_length=0.0,
    )

    monkeypatch.setattr("news_ingestor.storage.database.lay_quan_ly_db", lambda: db_mock)
    monkeypatch.setattr("news_ingestor.storage.repository.KhoTinTuc", lambda: repo_mock)
    monkeypatch.setattr(
        "news_ingestor.utils.evaluation.tao_bao_cao_pipeline",
        lambda ds_bai, so_ngay: bao_cao,
    )

    result = runner.invoke(cli, ["evaluate"])

    assert result.exit_code == 0
    assert "Evaluation summary" in result.output
