from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KafkaConfig:
    brokers: str
    topic: str
    sasl_username: str | None = None
    sasl_password: str | None = None
    sasl_mechanism: str = "PLAIN"
    security_protocol: str = "PLAINTEXT"
    ssl_ca_location: str | None = None
    batch_num_messages: int = 1000
    linger_ms: int = 50
    compression_type: str = "zstd"


class KafkaOutput:
    def __init__(self, config: KafkaConfig):
        self._config = config
        try:
            kafka_module = importlib.import_module("confluent_kafka")
            Producer = kafka_module.Producer
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("confluent-kafka is required for Kafka output") from exc

        producer_config: dict[str, Any] = {
            "bootstrap.servers": config.brokers,
            "batch.num.messages": config.batch_num_messages,
            "linger.ms": config.linger_ms,
            "compression.type": config.compression_type,
            "client.id": "news-ingestor",
        }

        if config.security_protocol:
            producer_config["security.protocol"] = config.security_protocol
        if config.sasl_username and config.sasl_password:
            producer_config["sasl.username"] = config.sasl_username
            producer_config["sasl.password"] = config.sasl_password
            producer_config["sasl.mechanism"] = config.sasl_mechanism
        if config.ssl_ca_location:
            producer_config["ssl.ca.location"] = config.ssl_ca_location

        self._producer = Producer(producer_config)

    def send(self, event: dict[str, Any]) -> None:
        key = str(event["event_id"]).encode("utf-8")
        payload = json.dumps(event, ensure_ascii=False, default=str).encode("utf-8")
        self._producer.produce(self._config.topic, key=key, value=payload)
        self._producer.poll(0)

    def flush(self, timeout: float = 5.0) -> None:
        self._producer.flush(timeout)
