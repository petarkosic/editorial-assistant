import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from langfuse import observe
from pydantic import BaseModel, Field

from common.config import MODEL_SCOUT
from common.gnews import decode_google_news_url
from common.llm import get_client, parse_json_response
from common.models import AnalysisResult, NewsArticle, ScoutReport
from scout_agent.tools import NewsFetcherTool

logger = logging.getLogger("scout_agent.agent")

# Kept small: each decode is a request to Google, which throttles bursts.
_MAX_PARALLEL_DECODES = 4

SYSTEM_PROMPT = """You are an assistant editor at a major news organization. Your sole task is to monitor incoming news feeds and identify the most important and breaking stories.

INSTRUCTIONS:
1. Analyze the provided list of recent news articles. Each has an integer "id", a title, a source, a publication date, and "related_articles" (how many other outlets cover the same story).
2. Ignore minor updates, trivial stories, and redundant information. Focus on impact, novelty, and public interest.
3. For each article that is important or breaking news (importance_score >= 5):
   - Refer to it by its "id", exactly as given.
   - Provide a RELEVANCE SCORE from 1-10 (10 is most important).
   - Write a concise ONE-SENTENCE SUMMARY of the story's significance.
   - Include brief reasoning for your score.
4. Return your analysis as a valid JSON array of objects. Do not repeat titles or links. If nothing is important, return [].

JSON FORMAT:
[
  {
    "id": 3,
    "importance_score": 8,
    "summary": "A concise sentence explaining the story's impact and why it matters.",
    "reasoning": "Brief explanation of why this score was assigned"
  }
]
"""


class _ScoutItem(BaseModel):
    """One finding as returned by the model. Only judgement, never article data."""

    id: int
    importance_score: int = Field(..., ge=1, le=10)
    summary: str
    reasoning: str | None = None


class NewsScoutAgent:
    """AI agent for scouting and analyzing news articles."""

    def __init__(self, client=None):
        self.client = client or get_client()
        self.news_fetcher = NewsFetcherTool()

    def analyze_articles(self, articles: list[NewsArticle]) -> list[AnalysisResult]:
        articles_data = [
            {
                "id": i,
                "title": a.title,
                "source": a.source,
                "pub_date": a.pub_date.isoformat() if a.pub_date else "Unknown",
                "related_articles": len(a.description),
            }
            for i, a in enumerate(articles)
        ]
        user_prompt = (
            "Please analyze the following batch of articles:\n\n"
            + json.dumps(articles_data, indent=2)
        )

        response = self.client.chat.completions.create(
            model=MODEL_SCOUT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        response_text = response.choices[0].message.content
        if not response_text:
            raise ValueError("Scout model returned an empty response")

        analysis_data = parse_json_response(response_text)
        if not isinstance(analysis_data, list):
            raise ValueError("Scout model did not return a JSON array of findings")

        articles_by_id = dict(enumerate(articles))
        seen: set[int] = set()
        results: list[AnalysisResult] = []
        for raw in analysis_data:
            item = _ScoutItem.model_validate(raw)
            article = articles_by_id.get(item.id)
            if article is None or item.id in seen:
                logger.warning(
                    "scout: ignoring finding with unknown or repeated id %s", item.id
                )
                continue

            seen.add(item.id)
            results.append(
                AnalysisResult(
                    importance_score=item.importance_score,
                    summary=item.summary,
                    original_title=article.title,
                    original_link=article.link,
                    reasoning=item.reasoning,
                    description=article.description,
                    source=article.source,
                    pub_date=article.pub_date,
                )
            )

        return results

    @observe(name="scout.generate_report")
    def generate_scout_report(self, rss_url: str) -> ScoutReport:
        """Raises on any failure (feed, LLM call, bad response).

        An empty `important_findings` therefore always means the scout ran and
        found nothing important - never that it failed. `original_link` is still
        the raw Google News link; call `resolve_original_links` for the real URL.
        """
        articles = self.news_fetcher.fetch_news_from_rss(rss_url)
        if not articles:
            raise RuntimeError("No news articles found in the feed.")

        analyses = self.analyze_articles(articles)
        important = [r for r in analyses if r.importance_score >= 5]

        return ScoutReport(
            generated_at=datetime.now(),
            analyzed_articles=len(articles),
            important_findings=important,
        )

    def resolve_original_links(self, report: ScoutReport) -> ScoutReport:
        """Decode each finding's Google News link to the publisher's URL, concurrently.

        Returns a new report and leaves the input untouched, so it can safely
        overlap with other readers of that report. Never raises: a link that
        can't be decoded is kept as-is.
        """
        findings = report.important_findings
        if not findings:
            return report

        with ThreadPoolExecutor(
            max_workers=min(len(findings), _MAX_PARALLEL_DECODES)
        ) as pool:
            links = list(
                pool.map(decode_google_news_url, (f.original_link for f in findings))
            )

        return report.model_copy(
            update={
                "important_findings": [
                    f.model_copy(update={"original_link": link})
                    for f, link in zip(findings, links)
                ]
            }
        )
