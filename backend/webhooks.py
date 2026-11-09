from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_S = 10
DEFAULT_TITLE = "🤖 Bug AI Detector Alert"
DISCORD_EMBED_COLOR = 15158332
DISCORD_TITLE_LIMIT = 256
DISCORD_DESCRIPTION_LIMIT = 4096
SLACK_TEXT_LIMIT = 40000


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _escape_slack(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _post_webhook(service: str, url: str, payload: dict[str, Any]) -> bool:
    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()
    except requests.HTTPError as exc:
        logger.warning("Webhook %s zwrócił HTTP %s", service, exc.response.status_code)
        return False
    except requests.RequestException as exc:
        logger.warning("Webhook %s nie powiódł się: %s", service, type(exc).__name__)
        return False
    return True


def send_slack_notification(message: str, title: str = DEFAULT_TITLE) -> bool:
    url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not url:
        return False

    text = f"*{_escape_slack(title)}*\n{_escape_slack(message)}"
    return _post_webhook("Slack", url, {"text": _truncate(text, SLACK_TEXT_LIMIT)})


def send_discord_notification(message: str, title: str = DEFAULT_TITLE) -> bool:
    url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if not url:
        return False

    payload = {
        "embeds": [
            {
                "title": _truncate(title, DISCORD_TITLE_LIMIT),
                "description": _truncate(message, DISCORD_DESCRIPTION_LIMIT),
                "color": DISCORD_EMBED_COLOR,
            }
        ],
        "allowed_mentions": {"parse": []},
    }
    return _post_webhook("Discord", url, payload)


def notify_all(message: str, title: str = DEFAULT_TITLE) -> dict[str, bool]:
    return {
        "slack": send_slack_notification(message, title),
        "discord": send_discord_notification(message, title),
    }
