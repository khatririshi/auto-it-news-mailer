#!/usr/bin/env python3

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import schedule

import config
from config import validate_config
from fetch_news import fetch_it_news
from filter_news import filter_news
from send_mail import send_email

LOG_FILE = Path(__file__).parent / "mailer.log"
STATE_FILE = Path(__file__).parent / "mailer_state.json"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _now_in_timezone(settings: config.Settings) -> datetime:
    return datetime.now(settings.timezone)


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _mark_sent_today(settings: config.Settings) -> None:
    now = _now_in_timezone(settings)
    _save_state(
        {
            "last_success_date": now.date().isoformat(),
            "last_success_at": now.isoformat(timespec="seconds"),
        }
    )


def _already_sent_today(settings: config.Settings) -> bool:
    state = _load_state()
    return state.get("last_success_date") == _now_in_timezone(settings).date().isoformat()


def _scheduled_time_reached(settings: config.Settings) -> bool:
    now = _now_in_timezone(settings)
    hour, minute = map(int, settings.send_time.split(":"))
    scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return now >= scheduled_time


def run_pipeline() -> None:
    settings = config.get_settings()
    logger.info("=" * 60)
    logger.info("Starting Auto IT News Mailer pipeline...")
    logger.info("=" * 60)

    raw_articles = fetch_it_news()
    if not raw_articles:
        logger.warning("No articles fetched. A no-news email will be sent.")

    articles = filter_news(raw_articles) if raw_articles else []
    if not articles:
        logger.warning("No IT articles after filtering. A no-news email will be sent.")

    success = send_email(articles)
    if success:
        _mark_sent_today(settings)
        logger.info("Pipeline completed at %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    else:
        logger.error("Pipeline finished but email was not sent.")


def _system_local_send_time(send_time: str, timezone_str: str) -> str:
    try:
        target_tz = ZoneInfo(timezone_str)
        system_tz = datetime.now().astimezone().tzinfo or ZoneInfo("UTC")
        today = datetime.now(target_tz).date()
        hour, minute = map(int, send_time.split(":"))
        target_dt = datetime(today.year, today.month, today.day, hour, minute, tzinfo=target_tz)
        return target_dt.astimezone(system_tz).strftime("%H:%M")
    except Exception:
        logger.warning(
            "Timezone conversion failed; using %s in local system time.",
            send_time,
        )
        return send_time


def start_scheduler() -> None:
    settings = config.get_settings()
    logger.info(
        "Scheduler started. Sending daily at %s %s.",
        settings.send_time,
        settings.timezone_str,
    )
    logger.info("   (Press Ctrl+C to stop)\n")

    try:
        schedule.every().day.at(settings.send_time, settings.timezone_str).do(run_pipeline)
    except (TypeError, ModuleNotFoundError, ImportError):
        local_time = _system_local_send_time(settings.send_time, settings.timezone_str)
        logger.warning(
            "Installed schedule library has no timezone argument; using %s local time instead.",
            local_time,
        )
        schedule.every().day.at(local_time).do(run_pipeline)

    if _already_sent_today(settings):
        logger.info("Today's digest was already sent. Waiting for the next scheduled run.")
    elif _scheduled_time_reached(settings):
        logger.info("Scheduled time already passed and no digest was sent today. Sending catch-up now...")
        run_pipeline()
    else:
        logger.info("Waiting for the first scheduled send at %s.", settings.send_time)

    while True:
        schedule.run_pending()
        time.sleep(60)


def main() -> None:
    try:
        validate_config()
    except EnvironmentError as exc:
        logger.error("Configuration error:\n%s", exc)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Auto IT News Mailer")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Send immediately instead of starting the scheduler",
    )
    args = parser.parse_args()

    if args.now:
        logger.info("--now flag detected. Sending immediately...")
        run_pipeline()
    else:
        start_scheduler()


if __name__ == "__main__":
    main()
