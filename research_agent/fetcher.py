import hashlib
import os
import re

import requests
from bs4 import BeautifulSoup

from common.config import FETCH_CHAR_CAP, FETCH_TIMEOUT_SECONDS, FETCH_USER_AGENT, REPO_ROOT
from common.models import SourceDocument

_PAYWALL_MARKERS = (
    "subscribe now",
    "subscribe to continue",
    "sign in to continue reading",
    "this content is for subscribers",
    "create a free account to continue",
)

_STRIP_TAGS = ("script", "style", "nav", "header", "footer")


def _url_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _read_captured(url: str) -> str | None:
    """Read a captured fixture for `url` when EVAL_MODE=1."""

    case_id = os.getenv("EVAL_CASE_ID")
    if not case_id:
        return None

    matches = sorted(
        (REPO_ROOT / "evals" / "dataset" / "sources" / case_id).glob(
            f"*/{_url_hash(url)}.txt"
        )
    )

    if not matches:
        return None

    return matches[0].read_text(encoding="utf-8")


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
            
    text = soup.get_text(separator=" ", strip=True)
    
    return re.sub(r"\s+", " ", text).strip()


def _looks_paywalled(text: str) -> bool:
    lowered = text.lower()

    return any(marker in lowered for marker in _PAYWALL_MARKERS)


class ArticleFetcherTool:
    """Fetches a URL's article text for the research agent's `fetch` tool.

    Never raises: every failure mode maps to a `SourceDocument.fetch_status`
    the calling loop can react to on its next turn.
    """

    def fetch(self, url: str) -> tuple[str, SourceDocument]:
        if os.getenv("EVAL_MODE") == "1":
            captured = _read_captured(url)
            if captured is None:
                return "", SourceDocument(url=url, fetch_status="error", char_count=0)
            capped = captured[:FETCH_CHAR_CAP]

            return capped, SourceDocument(url=url, fetch_status="ok", char_count=len(capped))

        try:
            response = requests.get(
                url,
                headers={"User-Agent": FETCH_USER_AGENT},
                timeout=FETCH_TIMEOUT_SECONDS,
            )
        except requests.Timeout:
            return "", SourceDocument(url=url, fetch_status="error", char_count=0)
        except requests.ConnectionError:
            return "", SourceDocument(url=url, fetch_status="error", char_count=0)
        except Exception:
            return "", SourceDocument(url=url, fetch_status="error", char_count=0)

        if response.status_code in (401, 403):
            return "", SourceDocument(url=url, fetch_status="blocked", char_count=0)
            
        if response.status_code != 200:
            return "", SourceDocument(url=url, fetch_status="error", char_count=0)

        text = _extract_text(response.text)
        if _looks_paywalled(text):
            return "", SourceDocument(url=url, fetch_status="blocked", char_count=0)

        capped = text[:FETCH_CHAR_CAP]

        return capped, SourceDocument(url=url, fetch_status="ok", char_count=len(capped))
