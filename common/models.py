from datetime import datetime

from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    title: str
    link: str
    pub_date: datetime | None = None
    source: str = "Unknown"
    description: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    importance_score: int = Field(..., ge=1, le=10)
    summary: str
    original_title: str
    original_link: str
    reasoning: str | None = None
    description: list[str] = Field(default_factory=list)
    source: str = "Unknown"
    pub_date: datetime | None = None


class ScoutReport(BaseModel):
    generated_at: datetime
    analyzed_articles: int
    important_findings: list[AnalysisResult]


class SourceDocument(BaseModel):
    url: str
    fetch_status: str  # "ok" | "blocked" | "error" | "skipped"
    char_count: int = 0


class ResearchBrief(BaseModel):
    background: str
    key_facts: list[str]
    open_questions: list[str]
    fact_check_flags: list[str]
    sources: list[SourceDocument]


class ArticleDraft(BaseModel):
    headline: str
    lede: str
    body: list[str]
    key_points: list[str]
    sources_cited: list[str]
    based_on_title: str
    generated_at: datetime
