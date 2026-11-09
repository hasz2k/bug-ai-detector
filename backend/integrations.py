from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT_S = 10
ERROR_BODY_LIMIT = 500
DEFAULT_LABELS = ("ai-detector", "automated-qa")


class ConfigError(RuntimeError):
    pass


class TrackerError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Brak wymaganej zmiennej środowiskowej: {name}")
    return value


@dataclass(frozen=True)
class JiraConfig:
    url: str
    email: str
    api_token: str
    project_key: str

    @classmethod
    def from_env(cls) -> JiraConfig:
        return cls(
            url=_require_env("JIRA_URL").rstrip("/"),
            email=_require_env("JIRA_EMAIL"),
            api_token=_require_env("JIRA_API_TOKEN"),
            project_key=os.getenv("JIRA_PROJECT_KEY", "BUG"),
        )


@dataclass(frozen=True)
class RedmineConfig:
    url: str
    api_key: str
    project_id: str

    @classmethod
    def from_env(cls) -> RedmineConfig:
        return cls(
            url=_require_env("REDMINE_URL").rstrip("/"),
            api_key=_require_env("REDMINE_API_KEY"),
            project_id=os.getenv("REDMINE_PROJECT_ID", "1"),
        )


def _post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    auth: tuple[str, str] | None = None,
) -> dict[str, Any]:
    try:
        response = requests.post(
            url, json=payload, headers=headers, auth=auth, timeout=REQUEST_TIMEOUT_S
        )
    except requests.RequestException as exc:
        raise TrackerError(f"Błąd połączenia z {url}: {exc}") from exc

    if not response.ok:
        body = response.text[:ERROR_BODY_LIMIT]
        raise TrackerError(
            f"{url} zwrócił {response.status_code}: {body}",
            status_code=response.status_code,
            body=body,
        )
    return response.json()


def _to_adf(text: str) -> dict[str, Any]:
    paragraphs = [
        {"type": "paragraph", "content": [{"type": "text", "text": line}]}
        for line in text.splitlines()
        if line.strip()
    ]
    return {"version": 1, "type": "doc", "content": paragraphs}


def create_jira_issue(
    summary: str,
    description: str,
    issue_type: str = "Bug",
    priority: str = "Medium",
    labels: list[str] | None = None,
    config: JiraConfig | None = None,
) -> dict[str, Any]:
    config = config or JiraConfig.from_env()
    payload = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": summary,
            "description": _to_adf(description),
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "labels": labels or list(DEFAULT_LABELS),
        }
    }
    return _post_json(
        f"{config.url}/rest/api/3/issue",
        payload,
        headers={"Accept": "application/json"},
        auth=(config.email, config.api_token),
    )


def create_redmine_issue(
    subject: str,
    description: str,
    tracker_id: int = 1,
    priority_id: int = 2,
    custom_fields: list[dict[str, Any]] | None = None,
    config: RedmineConfig | None = None,
) -> dict[str, Any]:
    config = config or RedmineConfig.from_env()
    issue: dict[str, Any] = {
        "project_id": config.project_id,
        "subject": subject,
        "description": description,
        "tracker_id": tracker_id,
        "priority_id": priority_id,
    }
    if custom_fields:
        issue["custom_fields"] = custom_fields

    return _post_json(
        f"{config.url}/issues.json",
        {"issue": issue},
        headers={"X-Redmine-API-Key": config.api_key},
    )
