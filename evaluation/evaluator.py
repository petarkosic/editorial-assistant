from datetime import datetime

from pydantic import BaseModel, Field

from common.config import MODEL_JUDGE
from common.llm import get_client, parse_json_response
from common.models import AnalysisResult, NewsArticle


class EvaluationScore(BaseModel):
    criterion: str
    score: int = Field(..., ge=1, le=5)
    reasoning: str


class ArticleEvaluation(BaseModel):
    article_title: str
    overall_score: float = Field(..., ge=1, le=5)
    scores: list[EvaluationScore]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: str


class EvaluationReport(BaseModel):
    evaluated_at: datetime
    total_articles: int
    average_score: float
    evaluations: list[ArticleEvaluation]
    overall_feedback: str


SYSTEM_PROMPT = """You are an expert evaluator assessing the quality of news article analysis performed by an AI assistant editor.

Evaluate the analysis on these criteria, each scored 1-5 (5 = excellent):
1. Importance Score Accuracy - is the 1-10 importance score appropriate?
2. Summary Quality - is the one-sentence summary clear and does it capture significance?
3. Reasoning Clarity - is the reasoning logical, specific, well-justified?
4. Consistency - does the score align with the summary and reasoning?
5. Relevance - was it correct to treat this as important news (score >= 5) or to filter it?

Return valid JSON:
{
  "article_title": "original title",
  "overall_score": 4.2,
  "scores": [{"criterion": "Importance Score Accuracy", "score": 4, "reasoning": "..."}],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": "..."
}
"""


class NewsScoutEvaluator:
    """LLM-as-a-Judge evaluator for News Scout Agent outputs."""

    def __init__(self, client=None):
        self.client = client or get_client()

    def evaluate_analysis(
        self, article: NewsArticle, analysis: AnalysisResult
    ) -> ArticleEvaluation:
        user_prompt = f"""Evaluate this analysis.

ORIGINAL ARTICLE:
Title: {article.title}
Source: {article.source}
Published: {article.pub_date}
Related links: {len(article.description)}

AI ANALYSIS:
Importance Score: {analysis.importance_score}/10
Summary: {analysis.summary}
Reasoning: {analysis.reasoning}
"""
        response = self.client.chat.completions.create(
            model=MODEL_JUDGE,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        eval_data = parse_json_response(response.choices[0].message.content)
        
        return ArticleEvaluation(**eval_data)
