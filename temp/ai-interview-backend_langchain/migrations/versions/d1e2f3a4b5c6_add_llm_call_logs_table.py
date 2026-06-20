"""add_llm_call_logs_table

Revision ID: d1e2f3a4b5c6
Revises: c3e4f5a6b7d8
Create Date: 2026-06-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c3e4f5a6b7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'llm_call_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('interview_id', sa.Integer(), nullable=True, comment='关联面试ID'),
        sa.Column('call_type', sa.String(50), nullable=False, comment='调用类型'),
        sa.Column('question_index', sa.Integer(), nullable=True, comment='题目序号'),
        sa.Column('model_name', sa.String(200), nullable=False, comment='模型名称'),
        sa.Column('temperature', sa.Float(), nullable=False, comment='温度参数'),
        sa.Column('request_messages', JSONB(), nullable=False, comment='请求消息'),
        sa.Column('response_content', sa.Text(), nullable=True, comment='响应内容'),
        sa.Column('prompt_tokens', sa.Integer(), server_default='0', comment='提示词Token数'),
        sa.Column('completion_tokens', sa.Integer(), server_default='0', comment='补全Token数'),
        sa.Column('total_tokens', sa.Integer(), server_default='0', comment='总Token数'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, comment='延迟(毫秒)'),
        sa.Column('status', sa.String(20), server_default='success', comment='状态'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('extra_metadata', JSONB(), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_llm_call_logs_id', 'llm_call_logs', ['id'])
    op.create_index('ix_llm_call_logs_interview_id', 'llm_call_logs', ['interview_id'])
    op.create_index('ix_llm_call_logs_call_type', 'llm_call_logs', ['call_type'])
    op.create_index('ix_llm_call_logs_model_name', 'llm_call_logs', ['model_name'])
    op.create_index('ix_llm_call_logs_created_at', 'llm_call_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('llm_call_logs')
