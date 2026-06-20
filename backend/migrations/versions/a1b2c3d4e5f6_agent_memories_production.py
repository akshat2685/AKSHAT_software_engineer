"""agent_memories production table (pgvector-ready)

Revision ID: a1b2c3d4e5f6
Revises: 2759970dfe52
Create Date: 2026-06-20 00:00:00.000000

Issue 3: provides a concurrent-safe, indexable memory store for production.
On PostgreSQL it uses JSONB content and a pgvector embedding column with an
ivfflat cosine index. On SQLite (local dev) it falls back to TEXT content
and skips the vector column so the migration still applies cleanly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2759970dfe52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name in {"postgresql", "postgres"}


def upgrade() -> None:
    bind = op.get_bind()

    if _is_postgres():
        # Enable pgvector extension (idempotent). Requires the extension to be
        # available on the server; if it isn't, the operator should install it
        # or drop the embedding column.
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")  # for gen_random_uuid()

        op.create_table(
            'agent_memories',
            sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True),
                      primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column('session_id', sa.String(100), nullable=False),
            sa.Column('agent_type', sa.String(50), nullable=False),
            sa.Column('memory_type', sa.String(50), nullable=False),
            sa.Column('content', sa.dialects.postgresql.JSONB, nullable=False),
            sa.Column('embedding', sa.Column, nullable=True),  # set via raw SQL below
            sa.Column('access_count', sa.Integer, server_default="0"),
            sa.Column('last_accessed', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text("NOW()")),
        )
        # Replace the placeholder embedding column with the real VECTOR type.
        op.execute("ALTER TABLE agent_memories DROP COLUMN embedding")
        op.execute("ALTER TABLE agent_memories ADD COLUMN embedding VECTOR(1536)")
        op.create_index('idx_memories_session', 'agent_memories', ['session_id'])
        op.execute(
            "CREATE INDEX idx_memories_embedding ON agent_memories "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        )
    else:
        # SQLite / others: store content and embedding as JSON/TEXT.
        op.create_table(
            'agent_memories',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('session_id', sa.String(100), nullable=False),
            sa.Column('agent_type', sa.String(50), nullable=False),
            sa.Column('memory_type', sa.String(50), nullable=False),
            sa.Column('content', sa.Text, nullable=False),
            sa.Column('embedding', sa.Text, nullable=True),
            sa.Column('access_count', sa.Integer, server_default="0"),
            sa.Column('last_accessed', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index('idx_memories_session', 'agent_memories', ['session_id'])


def downgrade() -> None:
    op.drop_index('idx_memories_session', table_name='agent_memories')
    try:
        op.drop_index('idx_memories_embedding', table_name='agent_memories')
    except Exception:
        pass
    op.drop_table('agent_memories')
