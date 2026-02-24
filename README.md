# tracking_news

News ingestor for Vietnam finance headlines. It parses RSS/Atom feeds, scores and tags events,
then publishes UTF-8 JSON messages to Kafka/Redpanda keyed by `event_id`.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,kafka]
news-ingestor run --once
```

Run daemon mode (default polling: 600 seconds):

```bash
news-ingestor run --daemon --interval-seconds 600
```

Backfill recent items:

```bash
news-ingestor backfill --minutes 120
```

## Configuration

Environment variables:

- `KAFKA_BROKERS` (default: `localhost:9092`)
- `KAFKA_TOPIC` (default: `news-events`)
- `KAFKA_SECURITY_PROTOCOL` (`PLAINTEXT`, `SASL_SSL`, etc.)
- `KAFKA_SASL_USERNAME`
- `KAFKA_SASL_PASSWORD`
- `KAFKA_SASL_MECHANISM` (default: `PLAIN`)
- `KAFKA_SSL_CA_LOCATION`
- `KAFKA_BATCH_NUM_MESSAGES` (default: `1000`)
- `KAFKA_LINGER_MS` (default: `50`)
- `KAFKA_COMPRESSION_TYPE` (default: `zstd`)
- `LOG_LEVEL` (default: `INFO`)

CLI options:

- `--feed-config` (default `config/feeds.json`)
- `--companies-file` (default `config/companies.txt`)
- `--log-level`

## Company-list workflow

1. Edit `config/companies.txt` and add one company per line.
2. Keep canonical names (e.g., `Vietcombank`, `FPT`, `Vingroup`).
3. Matching is accent-insensitive, so Vietnamese diacritics and ASCII variants both work.

## Scoring and taxonomy

Rules are deterministic and keyword based:

- Positive keywords: `profit`, `growth`, `record`, `upgrade`
- Negative keywords: `loss`, `fraud`, `downgrade`, `bankrupt`
- Rumor hints: `rumor`, `unverified`, `anonymous source`, `tin don`

Output fields:

- `taxonomy`: `positive`, `negative`, or `neutral`
- `score`: from `-1.0` to `1.0`
- `rumor`: boolean flag (halves the score magnitude)

## Example JSON output

```json
{
  "event_id": "9ff44d...",
  "source": "VN Finance RSS",
  "title": "FPT reports record profit growth",
  "summary": "Strong quarterly numbers.",
  "link": "https://example.com/news/1",
  "published_at": "2024-01-01T03:00:00+00:00",
  "companies": ["FPT"],
  "taxonomy": "positive",
  "score": 0.5,
  "rumor": false
}
```

## Docker compose

```bash
docker compose up --build
```

This starts:

- `redpanda` with healthcheck.
- `app` service running `news-ingestor run --daemon --interval-seconds 600`.

## Logging

The app emits structured JSON logs with timestamp, level, logger, message, and optional fields.
