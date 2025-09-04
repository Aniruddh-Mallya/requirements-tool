import os
import requests
import json

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

def _check_env():
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
        raise RuntimeError("Missing one or more Jira environment variables.")

def _clean_text(text):
    if not text:
        return ""
    return text.replace("\x00", "").strip()

def _adf(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text or ""}],
            }
        ],
    }

def create_issue(summary: str, description: str = "", labels: list[str] | None = None) -> dict:
    _check_env()
    url = JIRA_URL.rstrip("/") + "/rest/api/3/issue"
    summary = _clean_text(summary)[:255]
    description = _clean_text(description)
    labels = labels or []

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": _adf(description),
            "issuetype": {"name": "Story"},
            "labels": labels,
        }
    }
    r = requests.post(
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept":"application/json","Content-Type":"application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    if r.status_code in (200,201):
        return {"key": r.json().get("key"), "summary": summary}
    return {"error": f"Jira {r.status_code}: {r.text}"}
