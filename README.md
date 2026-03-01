# News Ingestor for Vietnamese Financial News

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Server-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated ingestion and NLP processing system for Vietnamese financial news, exposed via MCP tools for AI agents.

It collects news from multiple sources, fetches full article bodies, runs NLP (entity extraction, sentiment, impact scoring), stores structured data + vectors, and provides query tools through an MCP server.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [MCP Tools](#mcp-tools)
- [Configuration](#configuration)
- [Developer Commands](#developer-commands)
- [Dashboard](#dashboard)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Vietnamese Quickstart](#vietnamese-quickstart)

---

## Features

- Crawl from Vietnamese financial/news sources (CafeF, VnExpress, VietStock, RSS feeds).
- Fetch full article content from source URLs (not only feed snippets).
- NLP pipeline:
  - text cleaning
  - stock ticker/entity extraction
  - sentiment scoring/labeling
  - impact scoring and tags
  - optional embeddings for semantic search
- Persistence:
  - relational DB (SQLite by default, PostgreSQL optional)
  - vector DB (Qdrant)
- MCP server with tools for macro/company/sentiment/semantic queries.
- Structured logging + in-process metrics snapshot.
- Streamlit dashboard for monitoring.

---

## Architecture

```text
Crawlers -> Pipeline (clean + NER + sentiment + impact + embeddings)
         -> SQLite/PostgreSQL (metadata)
         -> Qdrant (vectors)

MCP Server exposes query tools for AI agents.
Dashboard reads from DB for monitoring/debugging.
```

---

## Quick Start

### 1) Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2) Configure

```bash
cp .env.example .env
```

Default `.env.example` is safe for local development (SQLite, no secrets).

### 3) Initialize database

```bash
news-ingestor init-db
```

### 4) Run one ingestion cycle

```bash
news-ingestor crawl --once
```

### 5) Check stats

```bash
news-ingestor stats
```

---

## CLI Commands

Main entrypoint: `news-ingestor`

- `news-ingestor init-db`
  - Initialize DB tables.
- `news-ingestor crawl --once`
  - Run one crawl cycle.
- `news-ingestor crawl --daemon --interval 900`
  - Run continuous crawl loop.
- `news-ingestor high-impact --days 3 --limit 20`
  - Show high-impact news.
- `news-ingestor stats`
  - Show system statistics.
- `news-ingestor evaluate --days 7 --limit 500`
  - Evaluate pipeline quality KPIs on recently ingested data.
- `news-ingestor serve-mcp`
  - Start MCP server over stdio.
- `news-ingestor demo`
  - Start Streamlit dashboard on an auto-selected free local port and print the URL.

Global options:

- `--log-level` (`DEBUG|INFO|WARNING|ERROR|CRITICAL`)
- `--json-log` (structured JSON logs)

---

## MCP Tools

The MCP server currently exposes:

1. `tim_tin_vi_mo`
2. `lay_tin_doanh_nghiep`
3. `tim_kiem_ngu_nghia`
4. `lay_cam_xuc_thi_truong`
5. `lay_metrics` (process metrics snapshot)

---

## Configuration

Key environment variables:

- `DATABASE_URL` (default: SQLite local file)
- `QDRANT_URL`
- `QDRANT_COLLECTION`
- `GEMINI_API_KEY` (optional)
- `EMBEDDING_MODEL`
- `CRAWL_INTERVAL_MINUTES`
- `REQUEST_TIMEOUT`
- `MAX_RETRIES`
- `USER_AGENT`
- `LOG_LEVEL`
- `METRICS_ENABLED`
- `TELEGRAM_ALERT_ENABLED`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Settings are validated in `config/settings.py`.

---

## Developer Commands

Using `Makefile`:

```bash
make lint
make format
make test
make run
make demo
```

Using scripts:

```bash
./scripts/lint.sh
./scripts/format.sh
./scripts/test.sh
./scripts/run.sh
./scripts/demo.sh
```

---

## Dashboard

- Manual launch:

```bash
streamlit run dashboard.py
```

- Auto-port launch via CLI:

```bash
news-ingestor demo
```

---

## Testing

```bash
python -m ruff check .
python -m pytest -q
```

## Evaluation

Pipeline quality summary:

```bash
news-ingestor evaluate --days 7 --limit 500
```

JSON output:

```bash
news-ingestor evaluate --days 7 --limit 500 --json-output
```

Detailed technical report:

- `docs/TECHNICAL_REPORT.md`

---

## Troubleshooting

- **`streamlit` not found when running `news-ingestor demo`**
  - Install dependencies: `pip install -e ".[dev]"`
- **No articles in DB**
  - Run `news-ingestor crawl --once` first.
- **Qdrant connection issues**
  - Verify `QDRANT_URL` and Qdrant service status.
- **Telegram alerts enabled but failing at startup**
  - If `TELEGRAM_ALERT_ENABLED=true`, both token and chat id must be set.

---

## Vietnamese Quickstart

### Mục tiêu
Chạy nhanh hệ thống thu thập tin tức tài chính với cấu hình an toàn mặc định.

### Các bước

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
news-ingestor init-db
news-ingestor crawl --once
news-ingestor stats
```

### Chạy dashboard demo (tự chọn cổng trống)

```bash
news-ingestor demo
```

Lệnh sẽ in URL local (ví dụ `http://127.0.0.1:<port>`).

### Chạy MCP server

```bash
news-ingestor serve-mcp
```

---

Built for practical financial-news ingestion and agent-ready querying.
