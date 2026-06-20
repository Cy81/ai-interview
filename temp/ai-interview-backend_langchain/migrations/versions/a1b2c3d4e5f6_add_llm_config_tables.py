"""add_llm_config_tables

Revision ID: a1b2c3d4e5f6
Revises: c7f982abaaf0
Create Date: 2026-06-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c7f982abaaf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 llm_providers 表
    op.create_table(
        'llm_providers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=False),
        sa.Column('api_key', sa.String(length=500), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_llm_providers_id'), 'llm_providers', ['id'], unique=False)

    # 创建 llm_models 表
    op.create_table(
        'llm_models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=200), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['provider_id'], ['llm_providers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('provider_id', 'model_name', name='uq_provider_model')
    )
    op.create_index(op.f('ix_llm_models_id'), 'llm_models', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_llm_models_id'), table_name='llm_models')
    op.drop_table('llm_models')
    op.drop_index(op.f('ix_llm_providers_id'), table_name='llm_providers')
    op.drop_table('llm_providers')
