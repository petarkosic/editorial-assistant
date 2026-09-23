import asyncio
import logging
import uuid
from urllib.parse import quote_plus

from sqlalchemy import select

from backend import repositories as repo
from backend.db import SessionLocal
from backend.models import Artifact, Evaluation, Run, Story
from backend.storage import get_store
from common.config import RESEARCH_CONCURRENCY
from common.models import AnalysisResult
from evaluation.judge import Judge
from research_agent.agent import ResearchAgent
from scout_agent.agent import NewsScoutAgent

logger = logging.getLogger("backend.pipeline")

_GNEWS = "https://news.google.com/rss"
_GNEWS_LOCALE = "hl=en-US&gl=US&ceid=US:en"


def build_rss_url(source_kind: str, source_query: str | None) -> str:
    """Build a Google News RSS URL from a run's source."""
    if source_kind == "top_stories":
        return f"{_GNEWS}?{_GNEWS_LOCALE}"

    if source_kind == "category":
        if not source_query:
            raise ValueError("a 'category' run requires source_query")

        topic = quote_plus(source_query.strip().upper())
        
        return f"{_GNEWS}/headlines/section/topic/{topic}?{_GNEWS_LOCALE}"
        
    if source_kind == "search":
        if not source_query:
            raise ValueError("a 'search' run requires source_query")
        return f"{_GNEWS}/search?q={quote_plus(source_query.strip())}&{_GNEWS_LOCALE}"

    raise ValueError(f"unknown source_kind: {source_kind!r}")


_semaphore = asyncio.Semaphore(RESEARCH_CONCURRENCY)
_background_tasks: set[asyncio.Task] = set()


async def _bounded(coro):
    async with _semaphore:
        return await coro


def enqueue(coro) -> asyncio.Task:
    """Schedule a coroutine on the running loop behind the concurrency semaphore."""
    task = asyncio.create_task(_bounded(coro))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return task


def _spawn(coro) -> asyncio.Task:
    """Schedule a coroutine WITHOUT the semaphore (already-bounded work)."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return task


async def run_in_thread(fn, *args):
    """Run a synchronous callable in the default thread pool."""
    loop = asyncio.get_running_loop()
    
    return await loop.run_in_executor(None, fn, *args)


async def run_scout_task(run_id: str, session_factory=SessionLocal) -> None:
    """Background scout stage: RSS -> agent -> judge -> artifact + story rows.

    Uses its own DB session (never a request session). Judge failure is
    non-blocking; any other failure sets run.status='failed'.
    """
    async with session_factory() as session:
        run = await session.get(Run, uuid.UUID(str(run_id)))
        if run is None:
            logger.warning("run_scout_task: run %s not found", run_id)
            return

        try:
            run.status = "scouting"
            await session.commit()

            rss_url = build_rss_url(run.source_kind, run.source_query)
            report = await run_in_thread(
                NewsScoutAgent().generate_scout_report, rss_url
            )
            report_json = report.model_dump(mode="json")

            store = get_store()
            file_key = f"{run_id}/scout_report.json"
            await run_in_thread(store.write_json, file_key, report_json)
            session.add(
                Artifact(
                    run_id=run.id,
                    story_id=None,
                    kind="scout_report",
                    file_key=file_key,
                    content=report_json,
                )
            )

            try:
                stage_eval = await run_in_thread(Judge().evaluate_scout, report)
                session.add(
                    Evaluation(
                        run_id=run.id,
                        story_id=None,
                        stage="scout",
                        overall_score=stage_eval.overall_score,
                        scores=[s.model_dump() for s in stage_eval.scores],
                        strengths=list(stage_eval.strengths),
                        weaknesses=list(stage_eval.weaknesses),
                        suggestions=stage_eval.suggestions,
                    )
                )
            except Exception:
                logger.exception(
                    "scout judge failed for run %s - continuing (advisory only)",
                    run_id,
                )

            for finding in report.important_findings:
                session.add(
                    Story(
                        run_id=run.id,
                        finding=finding.model_dump(mode="json"),
                        selected=False,
                        status="pending",
                    )
                )

            run.status = "selecting"
            await session.commit()
            logger.info(
                "scout task complete for run %s: %d stories",
                run_id,
                len(report.important_findings),
            )
        except Exception as exc:  # hard failure -> fail the run
            logger.exception("scout task failed for run %s", run_id)
            await session.rollback()
            run = await session.get(Run, uuid.UUID(str(run_id)))
            if run is not None:
                run.status = "failed"
                run.error = str(exc)
                await session.commit()


def _make_trace_callback(
    run_id: str, story_id: str, loop: asyncio.AbstractEventLoop, session_factory=SessionLocal
):
    """Builds the on_tool_call callback passed into ResearchAgent.research_story.

    Runs inside run_in_thread's worker thread. The shared `engine` (and its
    asyncpg connection pool) is bound to the *main* event loop, so a plain
    `asyncio.run()` here (which would spin up a second, unrelated event loop
    in this thread) fails with "attached to a different loop" the moment it
    touches a pooled connection. Instead, hand the write back to the real
    main loop via `run_coroutine_threadsafe` and block this worker thread on
    the result - correct, and still genuinely incremental (the caller sees
    the write complete before the next tool call runs).
    """

    def _on_tool_call(entry: dict) -> None:
        async def _write():
            async with session_factory() as session:
                existing = await repo.get_research_trace_artifact(session, uuid.UUID(story_id))
                calls = list(existing.content.get("tool_calls", [])) if existing else []
                calls.append(entry)

                await repo.upsert_artifact(
                    session,
                    uuid.UUID(run_id),
                    uuid.UUID(story_id),
                    "research_trace",
                    f"{run_id}/{story_id}/research_trace.json",
                    {"tool_calls": calls},
                )

                await session.commit()

        asyncio.run_coroutine_threadsafe(_write(), loop).result()

    return _on_tool_call


async def run_research_task(story_id: str, session_factory=SessionLocal) -> None:
    """Background research stage: agentic tool-calling loop -> brief + trace
    artifacts -> judge -> story.status transition.

    Concurrency is bounded by whatever scheduled this coroutine
    (enqueue_research_for_run uses pipeline.enqueue(), which already wraps the
    coroutine with the module-level semaphore) - this task does not acquire
    the semaphore itself, to avoid a double-acquisition deadlock risk.
    """

    async with session_factory() as session:
        story = await session.get(Story, uuid.UUID(str(story_id)))
        
        if story is None:
            logger.warning("run_research_task: story %s not found", story_id)

            return

        run_id = str(story.run_id)

        try:
            story.status = "researching"
            await session.commit()

            finding = AnalysisResult.model_validate(story.finding)
            loop = asyncio.get_running_loop()
            on_tool_call = _make_trace_callback(run_id, story_id, loop, session_factory)
            agent = ResearchAgent()
            brief = await run_in_thread(agent.research_story, finding, on_tool_call)
            trace = list(agent.last_trace)

            store = get_store()
            brief_json = brief.model_dump(mode="json")
            brief_key = f"{run_id}/{story_id}/research_brief.json"
            trace_key = f"{run_id}/{story_id}/research_trace.json"
            trace_json = {"tool_calls": trace}
            await run_in_thread(store.write_json, brief_key, brief_json)
            await run_in_thread(store.write_json, trace_key, trace_json)

            await repo.upsert_artifact(
                session, story.run_id, story.id, "research_brief", brief_key, brief_json
            )
            await repo.upsert_artifact(
                session, story.run_id, story.id, "research_trace", trace_key, trace_json
            )

            try:
                stage_eval = await run_in_thread(
                    Judge().evaluate_research, brief, finding, trace
                )
                session.add(
                    Evaluation(
                        run_id=story.run_id,
                        story_id=story.id,
                        stage="research",
                        overall_score=stage_eval.overall_score,
                        scores=[s.model_dump() for s in stage_eval.scores],
                        strengths=list(stage_eval.strengths),
                        weaknesses=list(stage_eval.weaknesses),
                        suggestions=stage_eval.suggestions,
                    )
                )
            except Exception:
                logger.exception(
                    "research judge failed for story %s - continuing (advisory only)",
                    story_id,
                )

            story.status = "research_ready"
            await session.commit()
        except Exception as exc:
            logger.exception("research task failed for story %s", story_id)
            await session.rollback()
            story = await session.get(Story, uuid.UUID(str(story_id)))
            if story is not None:
                story.status = "failed"
                story.error = str(exc)
                await session.commit()


async def enqueue_research_for_run(session, run_id) -> None:
    """Enqueues research only for newly-selected, still-`pending` stories -
    never re-enqueues a story whose research already started/finished, so
    calling this again later (selecting more stories mid-run) is safe."""

    run = await session.get(Run, uuid.UUID(str(run_id)))
    if run is None:
        return
    
    stories = (
        await session.execute(
            select(Story).where(
                Story.run_id == run.id,
                Story.selected.is_(True),
                Story.status == "pending",
            )
        )
    ).scalars().all()

    run.status = "in_progress"
    await session.commit()

    for story in stories:
        enqueue(run_research_task(str(story.id)))


def enqueue_synthesis_for_story(story_id: str) -> None:
    # replace this body with the real synthesis task enqueue. 
    logger.info("synthesis enqueue for story %s ", story_id)


async def reconcile_orphans(session_factory=SessionLocal) -> None:
    """Startup sweep: a story stuck mid-stage was orphaned by a restart."""
    async with session_factory() as session:
        orphans = (
            await session.execute(
                select(Story).where(Story.status.in_(["researching", "synthesizing"]))
            )
        ).scalars().all()

        for story in orphans:
            story.status = "failed"
            story.error = "interrupted by restart"

        await session.commit()
