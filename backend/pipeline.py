import asyncio
import logging
import uuid
from urllib.parse import quote_plus

from backend.db import SessionLocal
from backend.models import Artifact, Evaluation, Run, Story
from backend.storage import get_store
from common.config import RESEARCH_CONCURRENCY
from evaluation.judge import Judge
from scout_agent.agent import NewsScoutAgent

logger = logging.getLogger("backend.pipeline")

_GNEWS = "https://news.google.com/rss"
_GNEWS_LOCALE = "hl=en-US&gl=US&ceid=US:en"


def build_rss_url(source_kind: str, source_query: str | None) -> str:
    """Build a Google News RSS URL from a run's source (spec Section 4)."""
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
