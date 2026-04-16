import html
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import config
from filter_news import group_by_category

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent / "template.html"

CATEGORY_COLORS = {
    "AI & Machine Learning": {"bg": "#4a148c", "light": "#ce93d8"},
    "Cybersecurity": {"bg": "#b71c1c", "light": "#ef9a9a"},
    "Dev & Open Source": {"bg": "#1b5e20", "light": "#a5d6a7"},
    "Gadgets & Hardware": {"bg": "#e65100", "light": "#ffcc80"},
    "Startups & Business": {"bg": "#006064", "light": "#80deea"},
    "General Tech": {"bg": "#1565c0", "light": "#90caf9"},
}

SOURCE_COLORS = {
    "default": "#1565c0",
    "ai": "#7c4dff",
    "security": "#d32f2f",
    "dev": "#2e7d32",
    "gadgets": "#ef6c00",
    "startup": "#00838f",
}


def _pick_badge_color(source: str) -> str:
    lowered = source.lower()
    if any(keyword in lowered for keyword in ["ai", "machine", "openai", "deepmind"]):
        return SOURCE_COLORS["ai"]
    if any(keyword in lowered for keyword in ["security", "cyber", "hack", "threat"]):
        return SOURCE_COLORS["security"]
    if any(keyword in lowered for keyword in ["dev", "code", "github", "stack"]):
        return SOURCE_COLORS["dev"]
    if any(keyword in lowered for keyword in ["gadget", "verge", "engadget", "wired"]):
        return SOURCE_COLORS["gadgets"]
    if any(keyword in lowered for keyword in ["startup", "crunch", "venture"]):
        return SOURCE_COLORS["startup"]
    return SOURCE_COLORS["default"]


def _build_category_header(category: str, count: int) -> str:
    colors = CATEGORY_COLORS.get(category, CATEGORY_COLORS["General Tech"])
    article_word = "article" if count == 1 else "articles"
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="margin-bottom:16px;margin-top:8px;">
      <tr>
        <td style="background-color:{colors['bg']};border-radius:8px;padding:10px 18px;">
          <span style="font-size:14px;font-weight:700;color:#ffffff;letter-spacing:0.3px;">
            {html.escape(category)}
          </span>
          <span style="font-size:12px;color:{colors['light']};margin-left:10px;">
            {count} {article_word}
          </span>
        </td>
      </tr>
    </table>
    """


def _build_article_html(article: dict) -> str:
    badge_color = _pick_badge_color(article["source"])
    title = html.escape(article["title"])
    description = html.escape(article["description"])
    source = html.escape(article["source"])
    published = html.escape(article["published_at"])
    url = html.escape(article["url"])
    image_url = article.get("image_url", "")

    image_block = ""
    if image_url:
        image_block = f"""
        <img src="{html.escape(image_url)}" alt="Article image" width="100%"
             style="display:block;width:100%;height:200px;object-fit:cover;
                    border-radius:8px 8px 0 0;margin-bottom:0;" />
        """

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background-color:#1e2130;border-radius:12px;
                  border:1px solid #2a2d3e;margin-bottom:16px;overflow:hidden;">
      <tr><td>
        {image_block}
        <div style="padding:18px 22px 22px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td>
                <span style="display:inline-block;background-color:{badge_color};
                             color:#ffffff;font-size:11px;font-weight:600;
                             padding:3px 10px;border-radius:20px;
                             text-transform:uppercase;letter-spacing:0.5px;">
                  {source}
                </span>
              </td>
              <td align="right">
                <span style="font-size:12px;color:#546e7a;">{published}</span>
              </td>
            </tr>
          </table>
          <h2 style="margin:12px 0 8px;font-size:17px;font-weight:700;
                     color:#e3e8f0;line-height:1.4;">{title}</h2>
          <p style="margin:0 0 16px;font-size:14px;color:#90a4ae;line-height:1.7;">
            {description}
          </p>
          <a href="{url}"
             style="display:inline-block;background:#1565c0;color:#ffffff;
                    text-decoration:none;font-size:13px;font-weight:600;
                    padding:10px 22px;border-radius:8px;letter-spacing:0.3px;">
            Read Full Article
          </a>
        </div>
      </td></tr>
    </table>
    """


def _build_email_html(articles: list[dict]) -> str:
    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    except (OSError, FileNotFoundError) as exc:
        logger.error("template.html not found: %s - using fallback.", exc)
        template = (
            "<!DOCTYPE html><html><body style=\"background:#0f1117;font-family:Arial;\">"
            "<div style=\"max-width:640px;margin:auto;padding:20px;\">"
            "<h1 style=\"color:#fff;\">Daily IT News - {{DATE}}</h1>"
            "<p style=\"color:#90caf9;\">{{ARTICLE_COUNT}} stories today</p>"
            "{{ARTICLES}}"
            "</div></body></html>"
        )

    today = datetime.now(config.get_settings().timezone).strftime("%A, %B %d, %Y")
    grouped = group_by_category(articles)

    sections = []
    for category, category_articles in grouped.items():
        sections.append(_build_category_header(category, len(category_articles)))
        for article in category_articles:
            sections.append(_build_article_html(article))

    summary = " | ".join(
        f"{category} ({len(category_articles)})"
        for category, category_articles in grouped.items()
    )
    articles_html = "".join(sections)

    return (
        template.replace("{{DATE}}", today)
        .replace("{{ARTICLE_COUNT}}", str(len(articles)))
        .replace("{{ARTICLES}}", articles_html)
        .replace("AI Â· Cybersecurity Â· Dev Â· Gadgets Â· Startups", summary)
        .replace("AI · Cybersecurity · Dev · Gadgets · Startups", summary)
    )


def _build_no_news_html(today: str) -> str:
    return f"""
    <html><body style="margin:0;padding:0;background-color:#0f1117;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background-color:#0f1117;padding:40px 20px;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0" border="0"
                 style="max-width:600px;width:100%;">
            <tr><td style="background:#1565c0;border-radius:16px 16px 0 0;
                           padding:36px 40px;text-align:center;">
              <h1 style="margin:0;font-size:26px;font-weight:700;color:#ffffff;">
                IT News Digest
              </h1>
              <p style="margin:8px 0 0;font-size:14px;color:#90caf9;">{html.escape(today)}</p>
            </td></tr>
            <tr><td style="background-color:#1a1d2e;border-radius:0 0 16px 16px;
                           padding:48px 40px;text-align:center;">
              <h2 style="margin:0 0 12px;font-size:22px;color:#e3e8f0;">
                No IT News Available Today
              </h2>
              <p style="margin:0;font-size:15px;color:#90a4ae;line-height:1.7;">
                NewsAPI returned no IT-related articles for the past 24 hours.
                Your digest will be back tomorrow.
              </p>
            </td></tr>
          </table>
        </td></tr>
      </table>
    </body></html>
    """


def send_email(articles: list[dict]) -> bool:
    settings = config.get_settings()
    today = datetime.now(settings.timezone).strftime("%A, %B %d, %Y")

    if not settings.sender_email or not settings.sender_password:
        logger.error("Sender email or app password is missing. Cannot send email.")
        return False

    if not settings.recipient_email:
        logger.error("RECIPIENT_EMAIL is not set. Cannot send email.")
        return False

    recipients = [value.strip() for value in settings.recipient_email.split(",") if value.strip()]
    if not recipients:
        logger.error("No valid recipient emails found.")
        return False

    message = MIMEMultipart("alternative")
    message["From"] = settings.sender_email
    message["To"] = ", ".join(recipients)

    if not articles:
        logger.warning("No articles found; sending a no-news email.")
        message["Subject"] = "IT News Digest - No News Today"
        plain = (
            f"IT News Digest - {today}\n\n"
            "No IT-related articles were available in the past 24 hours.\n"
            "Your digest will be back tomorrow."
        )
        message.attach(MIMEText(plain, "plain", "utf-8"))
        message.attach(MIMEText(_build_no_news_html(today), "html", "utf-8"))
    else:
        message["Subject"] = settings.email_subject
        grouped = group_by_category(articles)
        plain_parts = []
        for category, category_articles in grouped.items():
            plain_parts.append(f"\n-- {category} --")
            for index, article in enumerate(category_articles, 1):
                plain_parts.append(
                    f"{index}. {article['title']}\n"
                    f"   {article['source']} | {article['published_at']}\n"
                    f"   {article['description']}\n"
                    f"   {article['url']}"
                )
        plain = f"IT News Digest - {today}\n" + "\n".join(plain_parts)
        message.attach(MIMEText(plain, "plain", "utf-8"))
        message.attach(MIMEText(_build_email_html(articles), "html", "utf-8"))

    try:
        logger.info("Connecting to Gmail SMTP...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.sender_email, settings.sender_password)
            server.sendmail(settings.sender_email, recipients, message.as_string())

        logger.info("Email sent to: %s", ", ".join(recipients))
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail authentication failed. Use a Gmail App Password, not your normal password."
        )
    except smtplib.SMTPException as exc:
        logger.error("SMTP error: %s", exc)
    except Exception as exc:
        logger.exception("Unexpected error while sending email: %s", exc)

    return False
