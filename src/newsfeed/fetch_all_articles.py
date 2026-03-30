"""
@Author: Srini Yedluri
@Date: 3/25/26
@Time: 6:25 PM
@File: fetch_all_articles.py
"""
from datetime import datetime
from newsfeed.rss_feed import fetch_rss_articles
from newsfeed.api_feed import fetch_api_articles
from publisher import publisher
import logging
logger = logging.getLogger(__name__)

def fetch_all_articles() -> list[dict]:
    """
    This function will call two functions one fetching articles 
    based on rss feed and another based on api. It combines the response
    and will call kafka publisher to publish articles to confluent kafka.
    It does log all the final articles if we enable DEBUG level logging.
    :return: list of dictionaries with article information 
    """
    logger.info(f"\n[Scheduler] Running fetch job at {datetime.now()}")
    rss_articles = fetch_rss_articles()
    api_articles = fetch_api_articles()
    all_articles = rss_articles + api_articles
    logger.info(f"[Scheduler] Total articles fetched: {len(all_articles)}")
    if logger.level == logging.DEBUG:
        for rss_article in rss_articles:
            logger.debug(f"RSS Articles: {rss_article} ")

        for api_article in api_articles:
            logger.debug(f"API Articles: {api_article}", )

    if all_articles:
        publisher.publish_to_kafka(all_articles)

    return all_articles