import json
from datetime import datetime

from googlenewsdecoder import gnewsdecoder
from langfuse import observe

from common.config import MODEL_SCOUT
from common.llm import get_client, parse_json_response
from common.models import AnalysisResult, NewsArticle, ScoutReport
from scout_agent.tools import NewsFetcherTool

SYSTEM_PROMPT = """You are an assistant editor at a major news organization. Your sole task is to monitor incoming news feeds and identify the most important and breaking stories.

INSTRUCTIONS:
1. Analyze the provided list of recent news articles.
2. Ignore minor updates, trivial stories, and redundant information. Focus on impact, novelty, and public interest.
3. For each article that is important or breaking news (importance_score >= 5):
   - Provide a RELEVANCE SCORE from 1-10 (10 is most important).
   - Write a concise ONE-SENTENCE SUMMARY of the story's significance.
   - Include brief reasoning for your score.
4. Return your analysis as a valid JSON array of objects.

JSON FORMAT:
[
  {
    "importance_score": 8,
    "summary": "A concise sentence explaining the story's impact and why it matters.",
    "original_title": "The original headline here",
    "original_link": "The original link here",
    "reasoning": "Brief explanation of why this score was assigned",
    "description": ["Link to related news articles"]
  }
]
"""


class NewsScoutAgent:
    """AI agent for scouting and analyzing news articles."""

    def __init__(self, client=None):
        self.client = client or get_client()
        self.news_fetcher = NewsFetcherTool()

    def analyze_articles(self, articles: list[NewsArticle]) -> list[AnalysisResult]:
        articles_data = [
            {
                "title": a.title,
                "link": a.link,
                "source": a.source,
                "pub_date": a.pub_date.isoformat() if a.pub_date else "Unknown",
                "description": a.description,
            }
            for a in articles
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

        try:
            analysis_data = parse_json_response(response_text)
        except ValueError as exc:
            print(f"Error parsing AI response: {exc}")
            return []

        results: list[AnalysisResult] = []
        for item in analysis_data:
            original = next(
                (a for a in articles if a.title == item.get("original_title")), None
            )
            if original is None:
                continue
            results.append(
                AnalysisResult(
                    importance_score=item["importance_score"],
                    summary=item["summary"],
                    original_title=item["original_title"],
                    original_link=self.decode_google_news_url(item["original_link"]),
                    reasoning=item.get("reasoning"),
                    description=item.get("description", []),
                    source=original.source,
                    pub_date=original.pub_date,
                )
            )

        return results

    @observe(name="scout.generate_report")
    def generate_scout_report(self, rss_url: str) -> ScoutReport:
        """Never returns None: an empty ScoutReport signals failure."""
        try:
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
        except Exception as exc:
            print(f"Error generating scout report: {exc}")

            return ScoutReport(
                generated_at=datetime.now(), analyzed_articles=0, important_findings=[]
            )

    def decode_google_news_url(self, url: str) -> str:
        try:
            decoded = gnewsdecoder(url, interval=1)
            if decoded.get("status"):
                return decoded["decoded_url"]

            print(f"Error decoding URL {url}: {decoded.get('message')}")

            return url
        except Exception as exc:
            print(f"Exception decoding URL {url}: {exc}")
            
            return url
