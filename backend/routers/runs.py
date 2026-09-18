import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend import pipeline
from backend import repositories as repo
from backend.db import get_session
from backend.schemas import (
    CreateRunRequest,
    EvaluationOut,
    RunDetail,
    RunSummary,
    StoryOut,
)
from backend.storage import get_store

router = APIRouter(prefix="/runs", tags=["runs"])


def _parse_uuid(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError:
        raise HTTPException(status_code=404, detail="run not found")


def _summary(run, story_count: int = 0) -> RunSummary:
    return RunSummary(
        id=str(run.id),
        status=run.status,
        source_kind=run.source_kind,
        source_query=run.source_query,
        error=run.error,
        created_at=run.created_at,
        story_count=story_count,
    )


@router.post("", response_model=RunSummary, status_code=202)
async def create_run(
    body: CreateRunRequest,
    session: AsyncSession = Depends(get_session),
):
    run = await repo.create_run(session, body.source_kind, body.source_query)
    await session.flush()
    await session.commit()

    pipeline.enqueue(pipeline.run_scout_task(str(run.id)))
    
    return _summary(run, story_count=0)


@router.get("", response_model=list[RunSummary])
async def list_runs(
    session: AsyncSession = Depends(get_session),
):
    rows = await repo.list_runs(session)

    return [_summary(run, count) for run, count in rows]


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    run = await repo.get_run(session, _parse_uuid(run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    stories = await repo.get_stories_for_run(session, run.id)
    artifact = await repo.get_scout_artifact(session, run.id)
    evaluation = await repo.get_scout_evaluation(session, run.id)

    return RunDetail(
        id=str(run.id),
        status=run.status,
        source_kind=run.source_kind,
        source_query=run.source_query,
        error=run.error,
        created_at=run.created_at,
        stories=[
            StoryOut(
                id=str(s.id),
                status=s.status,
                selected=s.selected,
                finding=s.finding,
            )
            for s in stories
        ],
        scout_report=artifact.content if artifact is not None else None,
        scout_evaluation=(
            EvaluationOut(
                stage=evaluation.stage,
                overall_score=float(evaluation.overall_score),
                scores=list(evaluation.scores),
                strengths=list(evaluation.strengths),
                weaknesses=list(evaluation.weaknesses),
                suggestions=evaluation.suggestions,
            )
            if evaluation is not None
            else None
        ),
    )


@router.delete("/{run_id}", status_code=204)
async def delete_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    run = await repo.get_run(session, _parse_uuid(run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    get_store().delete_prefix(f"{run.id}/")

    await repo.delete_run(session, run)

    await session.commit()
