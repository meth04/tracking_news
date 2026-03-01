# Technical Report: Vietnamese Financial News Ingestor

## 1. Problem Statement

The system targets continuous collection and analysis of Vietnamese financial news for downstream decision support. The core requirements are:

- ingest from heterogeneous sources (RSS + site crawlers),
- reduce duplicate content,
- enrich articles with NLP signals (entities, sentiment, impact),
- expose machine-usable access (CLI/MCP) and operator-friendly monitoring (Streamlit).

## 2. System Architecture

The pipeline is implemented as a layered architecture:

1. **Acquisition layer** (`src/news_ingestor/crawlers/`): source-specific crawlers coordinated by scheduler.
2. **Processing layer** (`src/news_ingestor/processing/pipeline.py`): cleaning, entity extraction, sentiment, impact scoring, optional embeddings.
3. **Persistence layer** (`src/news_ingestor/storage/`): relational storage (SQLite/PostgreSQL) + vector storage (Qdrant).
4. **Serving layer**:
   - CLI (`src/news_ingestor/cli.py`) for operations and diagnostics,
   - MCP server (`src/news_ingestor/mcp_server/server.py`) for AI-agent integration,
   - dashboard (`dashboard.py`) for operational observability.

## 3. Data Model and Processing Logic

### 3.1 Core entities

- Raw article: `BaiBaoTho` (crawler output).
- Processed article: `BaiBao` with fields for normalized URL, title hash, sentiment, impact, ticker list, and vector ID.

### 3.2 Deduplication

Dedup is applied using two keys:

- canonical URL (`url_chuan_hoa`),
- normalized title hash (`tieu_de_hash`).

This design handles common tracking-query variants and duplicate headlines.

### 3.3 NLP stages

For each article, the pipeline performs:

1. optional full-content fetch from source URL,
2. text cleaning and summary generation,
3. entity/ticker extraction,
4. sentiment scoring and label assignment,
5. rule-based impact classification (`LOW|MEDIUM|HIGH`),
6. optional embedding generation and vector persistence.

## 4. Monitoring and Operations

### 4.1 Metrics and logs

The project includes in-process counters (`src/news_ingestor/utils/metrics.py`) for key events:

- ingestion and dedup counters,
- pipeline success/failure counters,
- alert success/failure counters,
- MCP request counters.

Structured logging is configured centrally (`src/news_ingestor/utils/logging_config.py`).

### 4.2 Dashboard capabilities

The dashboard supports:

- daily aggregation view,
- record list and detail inspection,
- pipeline diagnostics.

## 5. Evaluation Methodology

Evaluation is defined on two layers:

1. **Classifier evaluation (supervised subset)**
   - objective: measure impact-level prediction consistency.
   - metric: accuracy + confusion matrix over labels `LOW/MEDIUM/HIGH`.

2. **Pipeline quality evaluation (operational KPI)**
   - objective: measure data completeness and consistency in production-like runs.
   - metrics:
     - coverage ratios: content/summary/sentiment/ticker/vector,
     - sentiment distribution + average score,
     - impact distribution + high-impact ratio,
     - average lengths (original/summary),
     - source diversity.

## 6. Implemented Evaluation Code

### 6.1 Evaluation module

A dedicated evaluation module is added:

- `src/news_ingestor/utils/evaluation.py`

Main functions:

- `danh_gia_impact_classifier(...)`: computes accuracy and confusion matrix.
- `tao_bao_cao_pipeline(...)`: computes operational KPI report over a time window.

### 6.2 CLI integration

A new CLI command is added:

- `news-ingestor evaluate --days <N> --limit <M> [--json-output]`

This command summarizes pipeline quality using stored records.

### 6.3 Tests

Added unit tests:

- `tests/unit/test_evaluation.py`

Coverage includes:

- classifier accuracy/confusion calculations,
- KPI report generation with non-empty and empty datasets.

## 7. UI Issue Fix: Article Detail Container

### 7.1 Reported issue

In article detail view, the content frame used an upper height cap and internal scrolling, which caused poor readability for long content.

### 7.2 Fix applied

In `dashboard.py` (detail page block):

- changed rendering to dynamic height without cap,
- switched `components.html(..., scrolling=False)` to avoid internal scroll container,
- retained proportional height estimate based on original/summary lengths.

Additionally, the detail HTML rendering now escapes article-derived text before injection into HTML.

## 8. Validation Plan

Recommended run sequence:

1. `python -m ruff check .`
2. `python -m pytest -q`
3. `python -m news_ingestor.cli evaluate --days 7`
4. `python -m news_ingestor.cli evaluate --days 7 --json-output`

For UI validation:

- run dashboard,
- open detail page with long article,
- verify container expands and no inner scrollbar appears in detail frame.

## 9. Current Limitations and Next Steps

1. Impact classifier is rule-based (v1); supervised calibration dataset should be expanded for robust threshold tuning.
2. KPI command currently evaluates persisted records only; scheduled historical reports can be added.
3. Optional extension: export periodic evaluation snapshots for trend tracking.

## 10. Conclusion

The system now includes a concrete evaluation framework (methodology + executable code) and an improved article detail UI aligned with readability requirements. This strengthens both **operational quality control** and **product usability** while preserving the existing architecture.
