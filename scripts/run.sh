#!/usr/bin/env bash
set -euo pipefail

python -m news_ingestor.cli crawl --once
