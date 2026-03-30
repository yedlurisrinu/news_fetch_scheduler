# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### Project Overview

News aggregation scheduler that fetches articles from RSS feeds and NewsAPI, deduplicates them, and publishes to an Apache Kafka topic every 30 minutes. Secrets are managed via HashiCorp Vault. Deployed as a Docker container.

### Common Commands

```bash
# Run tests with coverage
pytest --cov=src --cov-report=xml

# Run a single test file
pytest tests/path/to/test_file.py -v

# Run the app locally
PYTHONPATH=src python -m src.main

# Build Docker image
docker build -t news_fetch_scheduler:latest .

# Deploy with Docker Compose
docker-compose up -d
```

### Environment & Configuration

The app requires the following environment variables (loaded from Vault at `secret/NEWS_SUMMARY_APP`):

- `VAULT_ADDR` — Vault server URL (e.g. `http://vault-server:8200`)
- `VAULT_TOKEN` — Vault access token
- `VAULT_SECRET_PATH` — Secret path in Vault

Vault injects these into the OS environment at startup (dot-notation keys):
- `API.NEWS_API_KEY` — NewsAPI key
- `POSTGRES.host`, `POSTGRES.dbname`, `POSTGRES.user`, `POSTGRES.password`, `POSTGRES.port`
- `CONFLUENT.bootstrap.servers`, `CONFLUENT.sasl.username`, `CONFLUENT.sasl.password`, `CONFLUENT.client.id`

Static config (RSS feed URLs, Kafka topic, schedule interval) lives in `src/config/settings.py`.

### Architecture

```
main.py
  → sets up logging + loads Vault secrets
  → schedule_feed_fetch.schedule_fetch()
      → runs fetch_all_articles() immediately, then every 30 min
          → rss_feed.py       — parses BBC, Reuters, TechCrunch, Wired, Hacker News
          → api_feed.py       — fetches from NewsAPI (httpx async client)
          → publisher.py      — deduplicates and publishes to Kafka
              → article_deduplicator.py — two-tier dedup (in-memory + PostgreSQL)
```

### Deduplication

Articles are keyed by MD5 hash of `link + published_at + source`. Deduplication uses:

1. **In-memory set** — O(1) fast-path lookup
2. **PostgreSQL table `news_article_ids`** — persistent store; warmed into memory on startup with the last 2 days of hashes

An article is skipped if its hash exists in either tier. New hashes are written to both on publish.

### Kafka Publishing

- Topic: `news_ai_pipeline_dev_t_0` (6 partitions)
- Messages: JSON-serialized `Article` Pydantic model
- Message key: MD5 hash (for partition distribution)
- Transport: SASL_SSL with PLAIN auth (config in `src/resources/confluent-client.properties`)
- Flush happens after each full fetch cycle batch

### Custom Package Index

`requirements_locales.txt` installs `py-commons-per` from a local PyPI server at `http://localhost:8080/simple/`. This package provides `vault_secret_loader` and logging setup utilities used in `src/main.py`.

### Logging

Configured via `logging_config.json`. Logs go to both console (INFO) and `/app/logs/news_fetch_scheduler.log` (DEBUG). The logger namespace used in source files is `"my_project"`.

### CI/CD

`.github/workflows/ci-cd-yml` runs:
1. **Test** — on all pushes/PRs; runs pytest with coverage, uploads to Codecov
2. **Build** — on `main` branch only; builds and pushes Docker image to `ghcr.io` tagged as `latest` and the commit SHA
3. **Deploy** — stubbed out (not yet implemented)
