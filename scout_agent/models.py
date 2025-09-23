from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsArticle(BaseModel):
    title: str
    link: str
    pub_date: Optional[datetime] = None
    source: str = "Unknown"
    description: Optional[str] = None

class AnalysisResult(BaseModel):
    importance_score: int = Field(..., ge=1, le=10, description="Importance score between 1 and 10")
    summary: str = Field(..., description="One sentence summary of the article's significance")
    original_title: str = Field(..., description="The original title of the article")
    original_link: str = Field(..., description="The original link of the article")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the importance score")

class ScoutReport(BaseModel):
    generated_at: datetime
    analyzed_articles: int
    important_findings: List[AnalysisResult]
