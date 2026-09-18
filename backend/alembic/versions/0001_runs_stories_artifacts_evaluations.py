"""runs, stories, artifacts, evaluations

Revision ID: 0001
Revises:
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_uuid = postgresql.UUID(as_uuid=True)
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_kind", sa.String(), nullable=False),
        sa.Column("source_query", sa.String(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "stories",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column(
            "run_id",
            _uuid,
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("finding", postgresql.JSONB(), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_stories_run_id", "stories", ["run_id"])

    op.create_table(
        "artifacts",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column(
            "run_id",
            _uuid,
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "story_id",
            _uuid,
            sa.ForeignKey("stories.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("file_key", sa.String(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", _ts, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_artifacts_run_id", "artifacts", ["run_id"])

    op.create_table(
        "evaluations",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column(
            "run_id",
            _uuid,
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "story_id",
            _uuid,
            sa.ForeignKey("stories.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("overall_score", sa.Numeric(), nullable=False),
        sa.Column("scores", postgresql.JSONB(), nullable=False),
        sa.Column("strengths", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("weaknesses", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("suggestions", sa.Text(), nullable=False),
        sa.Column("created_at", _ts, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluations_run_id", "evaluations", ["run_id"])


def downgrade() -> None:
    op.drop_table("evaluations")
    op.drop_table("artifacts")
    op.drop_table("stories")
    op.drop_table("runs")
