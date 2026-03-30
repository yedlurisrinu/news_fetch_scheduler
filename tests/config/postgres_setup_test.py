"""
### Unit tests for src/config/postgres_setup.py
Tests that instantiate_connection passes the correct env-var-sourced
parameters to psycopg.connect and returns the connection object.
"""
import pytest
from unittest.mock import MagicMock, patch

from config.postgres_setup import instantiate_connection


_ENV = {
    "POSTGRES.host": "db-host",
    "POSTGRES.dbname": "news_db",
    "POSTGRES.user": "news_user",
    "POSTGRES.password": "s3cr3t",
    "POSTGRES.port": "5432",
}


class TestInstantiateConnection:

    ### Connection parameter mapping

    def test_passes_host_from_env(self):
        with patch("config.postgres_setup.psycopg.connect") as mock_connect, \
             patch("config.postgres_setup.os.getenv", side_effect=lambda k: _ENV.get(k)):
            instantiate_connection()

        assert mock_connect.call_args[1]["host"] == "db-host"

    def test_passes_dbname_from_env(self):
        with patch("config.postgres_setup.psycopg.connect") as mock_connect, \
             patch("config.postgres_setup.os.getenv", side_effect=lambda k: _ENV.get(k)):
            instantiate_connection()

        assert mock_connect.call_args[1]["dbname"] == "news_db"

    def test_passes_user_from_env(self):
        with patch("config.postgres_setup.psycopg.connect") as mock_connect, \
             patch("config.postgres_setup.os.getenv", side_effect=lambda k: _ENV.get(k)):
            instantiate_connection()

        assert mock_connect.call_args[1]["user"] == "news_user"

    def test_passes_password_from_env(self):
        with patch("config.postgres_setup.psycopg.connect") as mock_connect, \
             patch("config.postgres_setup.os.getenv", side_effect=lambda k: _ENV.get(k)):
            instantiate_connection()

        assert mock_connect.call_args[1]["password"] == "s3cr3t"

    def test_passes_port_from_env(self):
        with patch("config.postgres_setup.psycopg.connect") as mock_connect, \
             patch("config.postgres_setup.os.getenv", side_effect=lambda k: _ENV.get(k)):
            instantiate_connection()

        assert mock_connect.call_args[1]["port"] == "5432"

    ### Return value

    def test_returns_connection_object(self):
        mock_conn = MagicMock()
        with patch("config.postgres_setup.psycopg.connect", return_value=mock_conn), \
             patch("config.postgres_setup.os.getenv", side_effect=lambda k: _ENV.get(k)):
            result = instantiate_connection()

        assert result is mock_conn

    ### Missing env vars

    def test_passes_none_when_env_var_missing(self):
        with patch("config.postgres_setup.psycopg.connect") as mock_connect, \
             patch("config.postgres_setup.os.getenv", return_value=None):
            instantiate_connection()

        kwargs = mock_connect.call_args[1]
        assert kwargs["host"] is None
        assert kwargs["password"] is None