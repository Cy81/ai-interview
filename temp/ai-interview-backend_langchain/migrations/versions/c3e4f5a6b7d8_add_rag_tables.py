"""add_rag_tables

Revision ID: c3e4f5a6b7d8
Revises: b5d6e7f8a9b0
Create Date: 2026-06-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c3e4f5a6b7d8'
down_revision: Union[str, None] = 'b5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 启用 pgvector 扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 题库表
    op.create_table(
        'question_banks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(50), nullable=False, comment='分类'),
        sa.Column('position_tag', sa.String(100), nullable=True, comment='岗位标签'),
        sa.Column('difficulty', sa.String(20), server_default='medium', comment='难度'),
        sa.Column('question', sa.Text(), nullable=False, comment='题面'),
        sa.Column('reference_answer', sa.Text(), nullable=True, comment='参考答案'),
        sa.Column('key_points', JSONB(), nullable=True, comment='答题要点'),
        sa.Column('tags', JSONB(), nullable=True, comment='标签'),
        sa.Column('is_vectorized', sa.Boolean(), server_default='false', comment='是否已向量化'),
        sa.Column('usage_count', sa.Integer(), server_default='0', comment='使用次数'),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_question_banks_id', 'question_banks', ['id'])
    op.create_index('ix_question_banks_category', 'question_banks', ['category'])
    op.create_index('ix_question_banks_difficulty', 'question_banks', ['difficulty'])
    op.create_index('ix_question_banks_is_enabled', 'question_banks', ['is_enabled'])

    # 添加 embedding 列（使用原生 SQL 因为 pgvector 类型）
    op.execute('ALTER TABLE question_banks ADD COLUMN embedding vector(1024)')

    # 知识文档表
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False, comment='文档标题'),
        sa.Column('filename', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('doc_type', sa.String(50), nullable=False, comment='文档类型'),
        sa.Column('category', sa.String(100), nullable=True, comment='分类'),
        sa.Column('description', sa.Text(), nullable=True, comment='简介'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='文件存储路径'),
        sa.Column('file_size', sa.Integer(), server_default='0', comment='文件大小'),
        sa.Column('chunk_count', sa.Integer(), server_default='0', comment='分块数量'),
        sa.Column('is_vectorized', sa.Boolean(), server_default='false', comment='是否已向量化'),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_knowledge_documents_id', 'knowledge_documents', ['id'])
    op.create_index('ix_knowledge_documents_category', 'knowledge_documents', ['category'])
    op.create_index('ix_knowledge_documents_is_enabled', 'knowledge_documents', ['is_enabled'])

    # 知识分块表
    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False, comment='文档ID'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, comment='分块序号'),
        sa.Column('content', sa.Text(), nullable=False, comment='分块内容'),
        sa.Column('is_vectorized', sa.Boolean(), server_default='false', comment='是否已向量化'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_knowledge_chunks_id', 'knowledge_chunks', ['id'])
    op.create_index('ix_knowledge_chunks_document_id', 'knowledge_chunks', ['document_id'])

    # 添加 embedding 列
    op.execute('ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1024)')

    # 岗位模板表
    op.create_table(
        'position_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('position_tag', sa.String(100), nullable=False, comment='岗位标签'),
        sa.Column('title', sa.String(255), nullable=False, comment='标题'),
        sa.Column('category', sa.String(100), nullable=True, comment='分类'),
        sa.Column('level', sa.String(20), server_default='mid', comment='级别'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('core_skills', JSONB(), nullable=True, comment='核心技能'),
        sa.Column('interview_focus', sa.Text(), nullable=True, comment='面试重点'),
        sa.Column('recommended_difficulty', sa.String(20), server_default='medium', comment='推荐难度'),
        sa.Column('recommended_questions', sa.Integer(), server_default='5', comment='推荐题数'),
        sa.Column('key_evaluation_criteria', sa.Text(), nullable=True, comment='评估标准'),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_position_templates_id', 'position_templates', ['id'])
    op.create_index('ix_position_templates_position_tag', 'position_templates', ['position_tag'])
    op.create_index('ix_position_templates_is_enabled', 'position_templates', ['is_enabled'])


def downgrade() -> None:
    op.drop_table('position_templates')
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')
    op.drop_table('question_banks')
    op.execute('DROP EXTENSION IF EXISTS vector')
