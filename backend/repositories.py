import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Artifact, Evaluation, Run, Story


async def create_run(
    session: AsyncSession, source_kind: str, source_query: str | None
) -> Run:
    run = Run(status="scouting", source_kind=source_kind, source_query=source_query)
    session.add(run)
    
    return run


async def list_runs(session: AsyncSession) -> list[tuple[Run, int]]:
    stmt = (
        select(Run, func.count(Story.id))
        .outerjoin(Story, Story.run_id == Run.id)
        .group_by(Run.id)
        .order_by(Run.created_at.desc())
    )

    rows = (await session.execute(stmt)).all()

    return [(row[0], row[1]) for row in rows]


async def get_run(session: AsyncSession, run_id) -> Run | None:
    return (
        await session.execute(select(Run).where(Run.id == run_id))
    ).scalar_one_or_none()


async def get_stories_for_run(session: AsyncSession, run_id) -> list[Story]:
    return list(
        (
            await session.execute(
                select(Story)
                .where(Story.run_id == run_id)
                .order_by(Story.created_at.asc())
            )
        ).scalars()
    )


async def get_story(session: AsyncSession, story_id) -> Story | None:
    return (
        await session.execute(select(Story).where(Story.id == story_id))
    ).scalar_one_or_none()


async def get_scout_artifact(session: AsyncSession, run_id) -> Artifact | None:
    return (
        (
            await session.execute(
                select(Artifact)
                .where(Artifact.run_id == run_id, Artifact.kind == "scout_report")
                .order_by(Artifact.created_at.desc())
            )
        )
        .scalars()
        .first()
    )


async def get_scout_evaluation(session: AsyncSession, run_id) -> Evaluation | None:
    return (
        (
            await session.execute(
                select(Evaluation)
                .where(Evaluation.run_id == run_id, Evaluation.stage == "scout")
                .order_by(Evaluation.created_at.desc())
            )
        )
        .scalars()
        .first()
    )


async def delete_run(session: AsyncSession, run: Run) -> None:
    await session.delete(run)
