import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import dotenv_values

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
APP_CONFIG_FILE = BASE_DIR / "app_config.json"
LEGACY_APP_CONFIG_FILE = BASE_DIR / "app config.json"

NEWS_API_URL = "https://newsapi.org/v2/everything"
DEFAULT_EMAIL_SUBJECT = "Your Daily IT News Digest"
DEFAULT_MAX_ARTICLES = 8
DEFAULT_SEND_TIME = "08:00"
DEFAULT_LANGUAGE = "en"
DEFAULT_TIMEZONE_STR = "Asia/Kolkata"


@dataclass(frozen=True)
class Settings:
    news_api_key: str | None
    sender_email: str | None
    sender_password: str | None
    recipient_email: str | None
    email_subject: str
    max_articles: int
    send_time: str
    language: str
    timezone_str: str
    timezone: ZoneInfo


def _clean(value: object) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _read_app_config() -> dict:
    merged: dict = {}
    for path in (LEGACY_APP_CONFIG_FILE, APP_CONFIG_FILE):
        merged.update(_read_json_file(path))
    return merged


def _resolve_timezone(timezone_name: str) -> tuple[str, ZoneInfo]:
    try:
        return timezone_name, ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        logging.getLogger(__name__).warning(
            "Unknown timezone '%s'; falling back to UTC.", timezone_name
        )
        return "UTC", ZoneInfo("UTC")


def get_settings() -> Settings:
    env_values = {
        key: _clean(value)
        for key, value in dotenv_values(ENV_FILE).items()
    }
    app_cfg = _read_app_config()

    try:
        max_articles = int(app_cfg.get("max_articles", DEFAULT_MAX_ARTICLES))
    except (ValueError, TypeError):
        max_articles = DEFAULT_MAX_ARTICLES

    send_time = str(app_cfg.get("send_time", DEFAULT_SEND_TIME))
    timezone_name = _clean(app_cfg.get("timezone")) or DEFAULT_TIMEZONE_STR
    timezone_str, timezone = _resolve_timezone(timezone_name)

    return Settings(
        news_api_key=env_values.get("NEWS_API_KEY") or _clean(os.getenv("NEWS_API_KEY")),
        sender_email=env_values.get("SENDER_EMAIL") or _clean(os.getenv("SENDER_EMAIL")),
        sender_password=env_values.get("SENDER_PASSWORD") or _clean(os.getenv("SENDER_PASSWORD")),
        recipient_email=env_values.get("RECIPIENT_EMAIL") or _clean(os.getenv("RECIPIENT_EMAIL")),
        email_subject=(
            env_values.get("EMAIL_SUBJECT")
            or _clean(os.getenv("EMAIL_SUBJECT"))
            or DEFAULT_EMAIL_SUBJECT
        ),
        max_articles=max_articles,
        send_time=send_time,
        language=DEFAULT_LANGUAGE,
        timezone_str=timezone_str,
        timezone=timezone,
    )


def validate_config(settings: Settings | None = None) -> None:
    current = settings or get_settings()
    required = {
        "NEWS_API_KEY": current.news_api_key,
        "SENDER_EMAIL": current.sender_email,
        "SENDER_PASSWORD": current.sender_password,
        "RECIPIENT_EMAIL": current.recipient_email,
    }
    missing = [name for name, value in required.items() if not value]

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please check your .env file."
        )
