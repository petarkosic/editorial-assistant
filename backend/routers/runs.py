import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend import pipeline
from backend import repositories as repo
from backend.db import get_session
from backend.models import Evaluation, Story
from backend.schemas import (
    CreateRunRequest,
    EvaluationOut,
    RunDetail,
    RunSummary,
    SelectStoriesRequest,
    StoryDetail,
    StoryOut,
)
from backend.storage import get_store
from common.models import AnalysisResult, ResearchBrief
from evaluation.judge import Judge

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


async def _load_story_or_404(session, run_id: str, story_id: str) -> Story:
    try:
        run_uuid, story_uuid = uuid.UUID(run_id), uuid.UUID(story_id)
    except ValueError:
        raise HTTPException(404, detail="story not found")

    run = await repo.get_run(session, run_uuid)
    if run is None:
        raise HTTPException(404, detail="run not found")

    story = await repo.get_story(session, run_uuid, story_uuid)
    if story is None:
        raise HTTPException(404, detail="story not found")

    return story


async def _story_detail_response(session, story: Story) -> StoryDetail:
    brief_art = await repo.get_research_artifact(session, story.id)
    trace_art = await repo.get_research_trace_artifact(session, story.id)
    research_eval = await repo.get_research_evaluation(session, story.id)

    return StoryDetail(
        id=str(story.id),
        run_id=str(story.run_id),
        status=story.status,
        finding=story.finding,
        selected=story.selected,
        error=story.error,
        research_brief=brief_art.content if brief_art else None,
        research_trace=trace_art.content if trace_art else None,
        research_evaluation=(
            EvaluationOut.model_validate(research_eval, from_attributes=True)
            if research_eval else None
        ),
    )


@router.post("/{run_id}/select", status_code=202, response_model=RunDetail)
async def select_stories(
    run_id: str,
    body: SelectStoriesRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(404, detail="run not found")
        
    run = await repo.get_run(session, run_uuid)
    if run is None:
        raise HTTPException(404, detail="run not found")
    if run.status not in ("selecting", "in_progress"):
        raise HTTPException(409, detail=f"cannot select stories while run is {run.status!r}")

    try:
        story_uuids = [uuid.UUID(sid) for sid in body.story_ids]
    except ValueError:
        raise HTTPException(422, detail="story_ids must be valid uuids")

    await repo.mark_stories_selected(session, story_uuids)
    await session.commit()

    await pipeline.enqueue_research_for_run(session, run_id)

    stories = await repo.get_stories_for_run(session, run.id)
    scout_art = await repo.get_scout_artifact(session, run.id)
    scout_eval = await repo.get_scout_evaluation(session, run.id)

    return RunDetail(
        id=str(run.id), status=run.status, source_kind=run.source_kind,
        source_query=run.source_query, error=run.error, created_at=run.created_at,
        stories=[StoryOut.model_validate(s, from_attributes=True) for s in stories],
        scout_report=scout_art.content if scout_art else None,
        scout_evaluation=(
            EvaluationOut.model_validate(scout_eval, from_attributes=True) if scout_eval else None
        ),
    )


@router.get("/{run_id}/stories/{story_id}", response_model=StoryDetail)
async def get_story_detail(
    run_id: str, story_id: str, session: AsyncSession = Depends(get_session)
):
    story = await _load_story_or_404(session, run_id, story_id)
    
    return await _story_detail_response(session, story)


@router.post("/{run_id}/stories/{story_id}/approve", response_model=StoryDetail)
async def approve_story(
    run_id: str, story_id: str, session: AsyncSession = Depends(get_session)
):
    story = await _load_story_or_404(session, run_id, story_id)
    if story.status != "research_ready":
        raise HTTPException(409, detail=f"cannot approve a story in status {story.status!r}")
    story.status = "synthesizing"

    await session.commit()

    pipeline.enqueue_synthesis_for_story(str(story.id))

    return await _story_detail_response(session, story)


@router.post("/{run_id}/stories/{story_id}/reject", response_model=StoryDetail)
async def reject_story(
    run_id: str, story_id: str, session: AsyncSession = Depends(get_session)
):
    story = await _load_story_or_404(session, run_id, story_id)
    if story.status not in ("research_ready", "draft_ready"):
        raise HTTPException(409, detail=f"cannot reject a story in status {story.status!r}")
    story.status = "rejected"

    await session.commit()

    return await _story_detail_response(session, story)


@router.post("/{run_id}/stories/{story_id}/retry", response_model=StoryDetail)
async def retry_story(
    run_id: str, story_id: str, session: AsyncSession = Depends(get_session)
):
    story = await _load_story_or_404(session, run_id, story_id)
    if story.status != "failed":
        raise HTTPException(409, detail=f"cannot retry a story in status {story.status!r}")
    story.status = "researching"
    story.error = None

    await session.commit()

    pipeline.enqueue(pipeline.run_research_task(str(story.id)))

    return await _story_detail_response(session, story)


@router.post("/{run_id}/stories/{story_id}/evaluate", response_model=StoryDetail)
async def evaluate_story(
    run_id: str, story_id: str, session: AsyncSession = Depends(get_session)
):
    story = await _load_story_or_404(session, run_id, story_id)
    if story.status != "research_ready":
        raise HTTPException(409, detail=f"cannot evaluate a story in status {story.status!r}")

    brief_art = await repo.get_research_artifact(session, story.id)
    if brief_art is None:
        raise HTTPException(409, detail="no research brief to evaluate yet")

    finding = AnalysisResult.model_validate(story.finding)
    brief = ResearchBrief.model_validate(brief_art.content)
    trace_art = await repo.get_research_trace_artifact(session, story.id)
    trace = trace_art.content.get("tool_calls") if trace_art else None

    stage_eval = await pipeline.run_in_thread(
        Judge().evaluate_research, brief, finding, trace
    )

    existing = await repo.get_research_evaluation(session, story.id)
    if existing is not None:
        await session.delete(existing)
        await session.flush()

    session.add(
        Evaluation(
            run_id=story.run_id, story_id=story.id, stage="research",
            overall_score=stage_eval.overall_score,
            scores=[s.model_dump() for s in stage_eval.scores],
            strengths=list(stage_eval.strengths), weaknesses=list(stage_eval.weaknesses),
            suggestions=stage_eval.suggestions,
        )
    )

    await session.commit()

    return await _story_detail_response(session, story)
