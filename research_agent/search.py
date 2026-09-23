import hashlib
import json
import os

import requests

from common.config import REPO_ROOT, TAVILY_API_KEY

_TAVILY_URL = "https://api.tavily.com/search"


def _query_hash(query: str) -> str:
    return hashlib.sha1(query.encode("utf-8")).hexdigest()[:16]


def _read_captured_results(query: str) -> list[dict] | None:
    case_id = os.getenv("EVAL_CASE_ID")
    if not case_id:
        return None
    
    path = (
        REPO_ROOT
        / "evals"
        / "dataset"
        / "search_captures"
        / case_id
        / f"{_query_hash(query)}.json"
    )

    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
        
    return data.get("results", [])


def search(query: str) -> list[dict]:
    """Tavily-backed web search for the research agent's `search` tool.

    Never raises: any failure (network, non-200, malformed body) is treated
    as "no results" so the tool-calling loop reacts to it, not crashes on it.
    """
    if os.getenv("EVAL_MODE") == "1":
        return _read_captured_results(query) or []

    try:
        response = requests.post(
            _TAVILY_URL,
            json={"api_key": TAVILY_API_KEY, "query": query, "max_results": 5},
            timeout=10,
        )
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    try:
        body = response.json()
    except ValueError:
        return []

    raw_results = body.get("results")
    if not isinstance(raw_results, list):
        return []

    results = []
    for item in raw_results:
        try:
            results.append(
                {
                    "title": item["title"],
                    "url": item["url"],
                    "snippet": item.get("content", ""),
                }
            )
        except (KeyError, TypeError):
            continue
    return results
