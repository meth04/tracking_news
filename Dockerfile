FROM python:3.11-slim AS base

WORKDIR /app

# Cài đặt dependencies hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt dependencies Python
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY database ./database

RUN pip install --no-cache-dir -e .[postgres]

# Tạo thư mục data
RUN mkdir -p /app/data

# ============================================
# Stage: Crawler
# ============================================
FROM base AS crawler
CMD ["news-ingestor", "--log-level", "INFO", "crawl", "--daemon", "--interval", "900", "--no-embedding"]

# ============================================
# Stage: MCP Server
# ============================================
FROM base AS mcp-server
CMD ["news-ingestor", "serve-mcp"]

# ============================================
# Stage: Default (all-in-one)
# ============================================
FROM base AS default
CMD ["news-ingestor", "stats"]
