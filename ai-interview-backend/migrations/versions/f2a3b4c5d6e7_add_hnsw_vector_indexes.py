"""add hnsw vector indexes for RAG retrieval performance

Revision ID: f2a3b4c5d6e7
Revises: d1e2f3a4b5c6
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = "f2a3b4c5d6e7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # HNSW index for knowledge_chunks embedding (cosine distance)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # HNSW index for question_banks embedding (cosine distance)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_question_banks_embedding "
        "ON question_banks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    op.execute("DROP INDEX IF EXISTS ix_question_banks_embedding")
