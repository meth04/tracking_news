from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

from news_ingestor.pipeline import run_once


class InMemoryOutput:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def send(self, event: dict[str, object]) -> None:
        self.events.append(event)

    def flush(self, timeout: float = 5.0) -> None:
        _ = timeout


def test_e2e_smoke_with_local_http_fixture() -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(fixtures), **kwargs)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        output = InMemoryOutput()
        count = run_once([f"http://127.0.0.1:{port}/sample_rss.xml"], ["FPT"], output)
        server.shutdown()

    assert count == 1
    assert output.events[0]["event_id"]
    assert output.events[0]["companies"] == ["FPT"]
