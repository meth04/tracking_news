from __future__ import annotations

import argparse
import os

from news_ingestor.logging_utils import configure_logging
from news_ingestor.output.kafka import KafkaConfig, KafkaOutput
from news_ingestor.pipeline import (
    load_companies,
    load_feed_urls,
    run_backfill,
    run_daemon,
    run_once,
)


def build_output() -> KafkaOutput:
    config = KafkaConfig(
        brokers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        topic=os.getenv("KAFKA_TOPIC", "news-events"),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM", "PLAIN"),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        ssl_ca_location=os.getenv("KAFKA_SSL_CA_LOCATION"),
        batch_num_messages=int(os.getenv("KAFKA_BATCH_NUM_MESSAGES", "1000")),
        linger_ms=int(os.getenv("KAFKA_LINGER_MS", "50")),
        compression_type=os.getenv("KAFKA_COMPRESSION_TYPE", "zstd"),
    )
    return KafkaOutput(config)


def main() -> None:
    parser = argparse.ArgumentParser(prog="news-ingestor")
    parser.add_argument("--feed-config", default="config/feeds.json")
    parser.add_argument("--companies-file", default="config/companies.txt")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    mode = run_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--daemon", action="store_true")
    run_parser.add_argument("--interval-seconds", type=int, default=600)

    backfill_parser = subparsers.add_parser("backfill")
    backfill_parser.add_argument("--minutes", type=int, default=60)

    args = parser.parse_args()
    configure_logging(args.log_level)

    feed_urls = load_feed_urls(args.feed_config)
    companies = load_companies(args.companies_file)
    output = build_output()

    if args.command == "run":
        if args.once:
            run_once(feed_urls, companies, output)
        else:
            run_daemon(feed_urls, companies, output, args.interval_seconds)
    elif args.command == "backfill":
        run_backfill(feed_urls, companies, output, args.minutes)


if __name__ == "__main__":
    main()
