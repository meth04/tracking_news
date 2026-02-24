FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config

RUN pip install --no-cache-dir .[kafka]

CMD ["news-ingestor", "run", "--daemon", "--interval-seconds", "600"]
