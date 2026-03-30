import os

import httpx
from datetime import datetime, timezone
from config.settings import NEWS_API_URL, NEWS_API_PARAMS
import logging
from common.article import Article

logger = logging.getLogger(__name__)
def fetch_api_articles() -> list[dict]:
    """
        The function is responsible for fetching article information from APIs, parsing
        and creating model object.
        This needs NEWS_API_KEY be available in the environment, which will be loaded
        at application startup from vault server
        :return: list of Articles as dictionaries
        """
    articles = []
    try:
        params = {**NEWS_API_PARAMS, "apiKey": os.getenv('API.NEWS_API_KEY')}
        response = httpx.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        for item in data.get("articles", []):
            article_meta = {
                "title":      item.get("title", ""),
                "summary":    item.get("description", ""), # content
                "link":       item.get("url", ""),
                "published_at":  item.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                "source":     item.get("source", {}).get("name", "NewsAPI"),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }

            articles.append(Article(**article_meta).model_dump())
        logger.info(f"[API] Fetched {len(articles)} articles")
    except Exception as e:
        logger.error(f"[API] Failed to fetch articles: {e}", exc_info=True)
    return articles

