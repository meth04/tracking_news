from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

import pytest

from news_ingestor.output.kafka import KafkaConfig, KafkaOutput

pytest.importorskip("confluent_kafka")
from confluent_kafka import Consumer
from confluent_kafka.admin import AdminClient, NewTopic


def _wait_for_topic(client: AdminClient, topic: str) -> None:
    for _ in range(20):
        topics = client.list_topics(timeout=2).topics
        if topic in topics:
            return
        time.sleep(0.5)
    raise AssertionError("topic was not created")


def test_kafka_produce_consume_schema_and_key_validation() -> None:
    brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
    topic = f"news-events-it-{int(time.time())}"
    admin = AdminClient({"bootstrap.servers": brokers})
    fs = admin.create_topics([NewTopic(topic, 1, 1)])
    for future in fs.values():
        future.result(timeout=10)
    _wait_for_topic(admin, topic)

    output = KafkaOutput(KafkaConfig(brokers=brokers, topic=topic))
    event = {
        "event_id": "evt-123",
        "source": "test",
        "title": "hello",
        "summary": "world",
        "link": "https://example.com",
        "published_at": datetime.now(tz=timezone.utc).isoformat(),
        "companies": ["FPT"],
        "taxonomy": "neutral",
        "score": 0.0,
        "rumor": False,
    }
    output.send(event)
    output.flush()

    consumer = Consumer(
        {
            "bootstrap.servers": brokers,
            "group.id": f"g-{int(time.time())}",
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([topic])
    msg = consumer.poll(timeout=10)
    consumer.close()
    assert msg is not None and msg.error() is None
    assert msg.key().decode("utf-8") == "evt-123"
    payload = json.loads(msg.value().decode("utf-8"))
    assert payload["event_id"] == "evt-123"
    assert set(payload.keys()) >= {"event_id", "title", "taxonomy", "score"}
