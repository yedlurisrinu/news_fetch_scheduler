# News Fetch Scheduler

A Python service that aggregates news articles from multiple RSS feeds and the NewsAPI, deduplicates them against a PostgreSQL store, and publishes unique articles to an Apache Kafka topic on a configurable schedule.

---

### Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Demo](#demo)

---

### Overview

The scheduler wakes up every **30 minutes**, fetches articles from:

| Source | Type |
|---|---|
| BBC | RSS |
| Reuters | RSS |
| TechCrunch | RSS |
| Wired | RSS |
| Hacker News | RSS |
| NewsAPI | REST API |

Each article is identified by an MD5 hash of `link + published_at + source`. Articles already seen within the last 2 days (checked via an in-memory cache backed by PostgreSQL) are skipped. New articles are published as JSON messages to a Confluent Kafka topic.

---

### Architecture

```
main.py
  └── loads logging + Vault secrets
  └── schedule_feed_fetch.schedule_fetch()
        │
        ├── [on start + every 30 min]
        │
        └── fetch_all_articles()
              ├── rss_feed.fetch_rss_articles()     ← feedparser (BBC, Reuters, TechCrunch, Wired, HN)
              ├── api_feed.fetch_api_articles()      ← httpx → NewsAPI
              └── publisher.publish_to_kafka()
                    ├── _deduplicator()              ← lazy singleton: ArticleDeduplicator(psycopg conn)
                    │     ├── warm cache from PostgreSQL (last 2 days)
                    │     └── is_duplicate() / mark_seen()
                    └── _producer()                  ← lazy singleton: Confluent Kafka Producer
                          └── produce() → flush()
```

**Deduplication** uses a two-tier approach: an in-memory `set` for O(1) lookups, backed by a `news_article_ids` PostgreSQL table for durability across restarts.

**Lazy initialisation** — the PostgreSQL connection and Kafka producer are created on the first call to `publish_to_kafka` (via `@lru_cache` factories), not at import time. This keeps startup fast and makes the module side-effect-free.

---

### Prerequisites

| Dependency | Purpose |
|---|---|
| Python 3.12 | Runtime |
| PostgreSQL | Article deduplication state |
| Apache Kafka (Confluent) | Message queue |
| HashiCorp Vault | Secrets management |
| NewsAPI key | Top-headlines API |

The service expects two external Docker networks to exist:

```bash
docker network create vault-network
docker network create infra-network
```

---

### Configuration

All secrets are loaded from HashiCorp Vault at startup. Set the following environment variables before running:

| Variable | Description |
|---|---|
| `VAULT_ADDR` | Vault server URL (e.g. `http://vault-server:8200`) |
| `VAULT_TOKEN` | Vault access token |
| `VAULT_SECRET_PATH` | Path to the secret (e.g. `secret/NEWS_SUMMARY_APP`) |

The Vault secret must contain the following keys:

| Key | Description |
|---|---|
| `API.NEWS_API_KEY` | NewsAPI.org API key |
| `POSTGRES.host` | PostgreSQL host |
| `POSTGRES.dbname` | Database name |
| `POSTGRES.user` | Database user |
| `POSTGRES.password` | Database password |
| `POSTGRES.port` | Database port |
| `CONFLUENT.bootstrap.servers` | Kafka bootstrap server(s) |
| `CONFLUENT.sasl.username` | Kafka SASL username |
| `CONFLUENT.sasl.password` | Kafka SASL password |
| `CONFLUENT.client.id` | Kafka client ID |

Static settings (RSS feed URLs, Kafka topic name, schedule interval) are in `src/config/settings.py`.

The Kafka producer transport settings (SASL_SSL, timeouts, reconnect backoff) are in `src/resources/confluent-client.properties`.

---

### Running Locally

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Export required secrets
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=<your-token>
export VAULT_SECRET_PATH=secret/NEWS_SUMMARY_APP

# Run the scheduler
PYTHONPATH=src python -m src.main
```

Logs are written to both the console (INFO) and `/app/logs/news_fetch_scheduler.log`.

---

### Running with Docker

```bash
# Build the image
docker build -t news_fetch_scheduler:latest .

# Run with Docker Compose (requires vault-network and infra-network to exist)
VAULT_TOKEN=<your-token> docker compose up -d

# Tail logs
docker logs -f news_fetch_scheduler
```

The image uses a **multi-stage build** (builder → runtime) with a non-root `appuser` for security. The runtime stage contains only the installed packages and application source — no build tools.

**Health check:** Docker checks every 60 seconds that the Python process is running (`pgrep -f 'python.*main.py'`), with a 10-second timeout and 3 retries.

---

### Running Tests

```bash
# All tests with coverage
pytest --cov=src --cov-report=xml

# Single test file
pytest tests/publisher/publisher_test.py -v

# Single test case
pytest tests/common/utils_test.py::TestIsTruncated::test_short_summary_is_truncated -v
```

Tests use `pytest-mock` and `unittest.mock`. No real database, Kafka broker, or external HTTP calls are made — all infrastructure is mocked. The `tests/conftest.py` patches `psycopg.connect` and `confluent_kafka.Producer` at import time so that module-level initialisation in any source file is side-effect-free during the test run.

---

### Project Structure

```
news_fetch_scheduler/
├── src/
│   ├── main.py                          # Entry point — logging setup, Vault load, scheduler start
│   ├── scheduler/
│   │   └── schedule_feed_fetch.py       # Runs fetch immediately then every 30 min
│   ├── newsfeed/
│   │   ├── fetch_all_articles.py        # Orchestrates RSS + API fetch and Kafka publish
│   │   ├── rss_feed.py                  # feedparser-based RSS fetcher (5 feeds)
│   │   └── api_feed.py                  # httpx-based NewsAPI client
│   ├── publisher/
│   │   └── publisher.py                 # Dedup check + Kafka produce (lazy-init via lru_cache)
│   ├── article_dedup/
│   │   └── article_deduplicator.py      # Two-tier dedup: in-memory set + PostgreSQL
│   ├── common/
│   │   ├── article.py                   # Article Pydantic model
│   │   └── utils.py                     # generate_id (MD5), parse_to_iso, is_truncated
│   ├── config/
│   │   ├── settings.py                  # Static config: feeds, topic name, schedule interval
│   │   ├── postgres_setup.py            # psycopg connection factory
│   │   ├── confluent_producer_setup.py  # Confluent Kafka Producer factory
│   │   └── confluent_config.py          # .properties file parser
│   └── resources/
│       └── confluent-client.properties  # Kafka transport config (SASL_SSL, timeouts)
├── tests/                               # Mirrors src/ structure, filenames suffixed with _test
│   └── conftest.py                      # Session-level infrastructure mocks
├── demo/                                # Demo assets — see Demo section below
├── Dockerfile                           # Multi-stage build (builder + runtime)
├── docker-compose.yml                   # Service definition with Vault env vars
├── logging_config.json                  # Console + file handlers, DEBUG root level
├── pytest.ini                           # testpaths=tests, pythonpath=src
└── requirements.txt                     # Runtime + test dependencies
```

---

### Demo

> Demo assets (recordings, screenshots, and step-by-step walkthrough scripts) are located in the [`demo/`](./demo/) folder.

The demo folder will contain:

| File | Description |
|---|---|
| `demo/README.md` | Step-by-step instructions to run the demo end-to-end |
| `demo/*.cast` / `demo/*.gif` | Terminal recordings of the scheduler in action |
| `demo/*.png` | Screenshots of Kafka topic messages and PostgreSQL dedup table |

To play a terminal recording (`.cast` file) locally:

```bash
# Install asciinema if not already installed
pip install asciinema

asciinema play demo/<recording>.cast
```