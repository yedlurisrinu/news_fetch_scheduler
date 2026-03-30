"""
Root conftest.py — patches import-time side effects in publisher.py
(psycopg.connect and confluent_kafka.Producer) before test collection
so that modules with module-level initialisation can be safely imported.
"""
import atexit
from unittest.mock import MagicMock, patch

# Must start before test files are imported (i.e. at conftest import time)
_pg_patcher = patch("psycopg.connect", return_value=MagicMock())
_producer_patcher = patch("confluent_kafka.Producer", return_value=MagicMock())

_pg_patcher.start()
_producer_patcher.start()

atexit.register(_pg_patcher.stop)
atexit.register(_producer_patcher.stop)