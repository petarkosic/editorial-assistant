import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    source_kind: Literal["top_stories", "category", "search"]
    source_query: str | None = None


class StoryOut(BaseModel):
    id: uuid.UUID
    status: str
    selected: bool
    finding: dict


class EvaluationOut(BaseModel):
    stage: str
    overall_score: float
    scores: list[dict]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: str


class RunSummary(BaseModel):
    id: uuid.UUID
    status: str
    source_kind: str
    source_query: str | None = None
    error: str | None = None
    created_at: datetime
    story_count: int = 0


class RunDetail(BaseModel):
    id: uuid.UUID
    status: str
    source_kind: str
    source_query: str | None = None
    error: str | None = None
    created_at: datetime
    stories: list[StoryOut]
    scout_report: dict | None = None
    scout_evaluation: EvaluationOut | None = None


class SelectStoriesRequest(BaseModel):
    story_ids: list[str] = Field(..., min_length=1)


class StoryDetail(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    status: str
    finding: dict
    selected: bool
    error: str | None
    research_brief: dict | None = None
    research_trace: dict | None = None
    research_evaluation: EvaluationOut | None = None
    article_draft: dict | None = None
    draft_evaluation: EvaluationOut | None = None
