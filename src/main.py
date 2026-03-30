"""
@Author: Srini Yedluri
@Date: 3/21/26
@File: main.py
"""
"""
The main module that loads config, calling common
 module for setup logging and loading secrets from
 vault server that is running in docker on localhost.
 After successful completion it will schedule a job to
 fetch articles information periodically.
"""
from py_commons_per.logging_setup import setup_logging
# loads secretes from vault and set into environment variables
from py_commons_per.vault_secret_loader import load_secrets
from scheduler import schedule_feed_fetch

def main():
    setup_logging()
    load_secrets()
    schedule_feed_fetch.schedule_fetch()

main()