import logging
import time
from datetime import datetime, timedelta

import requests

import config

logger = logging.getLogger(__name__)

IT_SEARCH_QUERY = (
    "artificial intelligence OR cybersecurity OR programming OR "
    "software development OR startup technology OR gadgets OR "
    "machine learning OR cloud computing OR data breach OR "
    "open source OR developer tools"
)

MAX_RETRIES = 3
RETRY_DELAY = 5


def fetch_it_news() -> list[dict]:
    settings = config.get_settings()
    if not settings.news_api_key:
        logger.error("NEWS_API_KEY is not set. Cannot fetch news.")
        return []

    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "q": IT_SEARCH_QUERY,
        "language": settings.language,
        "sortBy": "publishedAt",
        "from": yesterday,
        "pageSize": settings.max_articles * 3,
        "apiKey": settings.news_api_key,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Fetching IT news from NewsAPI (attempt %d/%d)...",
                attempt,
                MAX_RETRIES,
            )
            response = requests.get(config.NEWS_API_URL, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            if data.get("status") != "ok":
                logger.error(
                    "NewsAPI returned status: %s - %s",
                    data.get("status"),
                    data.get("message", ""),
                )
                return []

            articles = data.get("articles", [])
            logger.info("Fetched %d raw articles.", len(articles))
            return articles

        except requests.exceptions.ConnectionError:
            logger.warning("Attempt %d: no internet connection.", attempt)
        except requests.exceptions.Timeout:
            logger.warning("Attempt %d: request to NewsAPI timed out.", attempt)
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error from NewsAPI: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Unexpected error while fetching news: %s", exc)
            return []

        if attempt < MAX_RETRIES:
            logger.info("Retrying in %d seconds...", RETRY_DELAY)
            time.sleep(RETRY_DELAY)

    logger.error("All %d fetch attempts failed.", MAX_RETRIES)
    return []
