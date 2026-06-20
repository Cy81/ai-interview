"""add md5_hash column to resumes for deduplication

Revision ID: g3h4i5j6k7l8
Revises: f2a3b4c5d6e7
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = "g3h4i5j6k7l8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("md5_hash", sa.String(32), nullable=True))
    op.create_index("ix_resumes_md5_hash", "resumes", ["md5_hash"])


def downgrade() -> None:
    op.drop_index("ix_resumes_md5_hash", table_name="resumes")
    op.drop_column("resumes", "md5_hash")
