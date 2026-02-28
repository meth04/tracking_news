PYTHON ?= python
MODULE ?= news_ingestor.cli

.PHONY: lint format test run demo

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check . --fix

test:
	$(PYTHON) -m pytest -q

run:
	$(PYTHON) -m $(MODULE) crawl --once

demo:
	$(PYTHON) -m $(MODULE) demo
