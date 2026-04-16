import logging
from datetime import datetime

import config

logger = logging.getLogger(__name__)

CATEGORIES = {
    "AI & Machine Learning": [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",
        "llm",
        "generative ai",
        "chatgpt",
        "openai",
        "claude",
        "gemini",
        "copilot",
        "ai model",
        "large language",
    ],
    "Cybersecurity": [
        "cybersecurity",
        "cyber attack",
        "data breach",
        "ransomware",
        "malware",
        "vulnerability",
        "hacker",
        "phishing",
        "zero-day",
        "encryption",
        "firewall",
        "infosec",
        "exploit",
    ],
    "Dev & Open Source": [
        "programming",
        "software",
        "developer",
        "open source",
        "github",
        "python",
        "javascript",
        "typescript",
        "framework",
        "api",
        "sdk",
        "devops",
        "kubernetes",
        "docker",
        "cloud",
        "coding",
    ],
    "Gadgets & Hardware": [
        "gadget",
        "smartphone",
        "chip",
        "processor",
        "nvidia",
        "amd",
        "apple silicon",
        "wearable",
        "gpu",
        "semiconductor",
        "hardware",
    ],
    "Startups & Business": [
        "startup",
        "tech company",
        "venture capital",
        "ipo",
        "funding round",
        "unicorn",
        "acquisition",
        "merger",
        "big tech",
        "valuation",
    ],
}

IT_KEYWORDS = [keyword for keywords in CATEGORIES.values() for keyword in keywords]
EXCLUDED_SOURCES = {"the sun", "daily mail", "buzzfeed", "tmz"}


def _get_category(article: dict) -> str:
    text = " ".join(
        [
            article.get("title") or "",
            article.get("description") or "",
            article.get("content") or "",
        ]
    ).lower()

    for category, keywords in CATEGORIES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "General Tech"


def _is_duplicate(title: str, seen_titles: list[str]) -> bool:
    words_new = set(title.lower().split())
    for seen in seen_titles:
        words_seen = set(seen.lower().split())
        if not words_new or not words_seen:
            continue

        overlap = len(words_new & words_seen) / max(len(words_new), len(words_seen))
        if overlap >= 0.55 and len(words_new) >= 4:
            return True
    return False


def _normalise(article: dict) -> dict:
    raw_date = article.get("publishedAt", "")
    try:
        dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ")
        published_at = dt.strftime("%B %d, %Y  %H:%M UTC")
    except ValueError:
        published_at = raw_date or "Unknown date"

    description = (
        article.get("description")
        or article.get("content")
        or "No description available."
    )
    if "[+" in description:
        description = description[: description.index("[+")].strip()

    return {
        "title": article.get("title") or "Untitled",
        "description": description,
        "source": (article.get("source") or {}).get("name") or "Unknown",
        "published_at": published_at,
        "url": article.get("url") or "#",
        "image_url": article.get("urlToImage") or "",
        "category": _get_category(article),
    }


def filter_news(raw_articles: list[dict]) -> list[dict]:
    filtered = []
    seen_titles: list[str] = []
    max_articles = config.get_settings().max_articles

    for article in raw_articles:
        if not article.get("title") or not article.get("url"):
            continue

        source_name = (article.get("source") or {}).get("name") or ""
        if source_name.lower() in EXCLUDED_SOURCES:
            continue

        text = " ".join(
            [
                article.get("title") or "",
                article.get("description") or "",
                article.get("content") or "",
            ]
        ).lower()
        if not any(keyword in text for keyword in IT_KEYWORDS):
            continue

        title = article.get("title", "")
        if _is_duplicate(title, seen_titles):
            logger.debug("Skipping duplicate: %s", title[:60])
            continue

        seen_titles.append(title)
        filtered.append(_normalise(article))

        if len(filtered) >= max_articles:
            break

    logger.info(
        "Filtered to %d unique IT articles across %d categories.",
        len(filtered),
        len({article["category"] for article in filtered}),
    )
    return filtered


def group_by_category(articles: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for category in list(CATEGORIES.keys()) + ["General Tech"]:
        bucket = [article for article in articles if article["category"] == category]
        if bucket:
            groups[category] = bucket
    return groups
