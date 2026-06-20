import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge_document import KnowledgeDocument, KnowledgeChunk
from app.models.question_bank import QuestionBank
from app.models.position_template import PositionTemplate
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RAGService:

    @staticmethod
    async def retrieve_knowledge(
        db: AsyncSession,
        query: str,
        category: str = None,
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """从知识库检索与查询相关的文档片段"""
        query_embedding = await embedding_service.get_embedding(query)
        if query_embedding is None:
            logger.warning("知识库检索：生成查询向量失败，跳过检索")
            return []

        # 构建过滤条件：已向化 + 所属文档已启用
        filters = [KnowledgeChunk.is_vectorized == True]  # noqa: E712

        # 获取已启用文档的 ID
        enabled_docs_query = select(KnowledgeDocument.id).where(
            KnowledgeDocument.is_enabled == True  # noqa: E712
        )
        if category:
            enabled_docs_query = enabled_docs_query.where(
                KnowledgeDocument.category == category
            )
        result = await db.execute(enabled_docs_query)
        doc_ids = [row[0] for row in result.all()]

        if not doc_ids:
            return []

        filters.append(KnowledgeChunk.document_id.in_(doc_ids))

        search_results = await embedding_service.vector_search(
            db, KnowledgeChunk, query_embedding, filters, top_k, min_score
        )

        # 加载父文档标题
        enriched = []
        for item in search_results:
            chunk: KnowledgeChunk = item["instance"]
            doc_result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == chunk.document_id)
            )
            doc = doc_result.scalar_one_or_none()
            enriched.append({
                "content": chunk.content,
                "document_title": doc.title if doc else "未知文档",
                "similarity_score": item["similarity_score"],
            })

        return enriched

    @staticmethod
    async def retrieve_questions(
        db: AsyncSession,
        query: str,
        position_tag: str = None,
        difficulty: str = None,
        top_k: int = 3,
        min_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """从题库检索与查询相关的参考题目"""
        query_embedding = await embedding_service.get_embedding(query)
        if query_embedding is None:
            logger.warning("题库检索：生成查询向量失败，跳过检索")
            return []

        filters = [QuestionBank.is_enabled == True]  # noqa: E712

        if position_tag:
            filters.append(QuestionBank.position_tag == position_tag)
        if difficulty:
            filters.append(QuestionBank.difficulty == difficulty)

        search_results = await embedding_service.vector_search(
            db, QuestionBank, query_embedding, filters, top_k, min_score
        )

        enriched = []
        for item in search_results:
            q: QuestionBank = item["instance"]
            enriched.append({
                "instance": q,
                "question": q.question,
                "category": q.category,
                "difficulty": q.difficulty,
                "similarity_score": item["similarity_score"],
            })

        return enriched

    @staticmethod
    async def get_position_template(
        db: AsyncSession,
        position_tag: str,
    ) -> Optional[PositionTemplate]:
        """根据岗位标签查找匹配的岗位模板，优先精确匹配"""
        # 精确匹配
        result = await db.execute(
            select(PositionTemplate).where(
                PositionTemplate.position_tag == position_tag,
                PositionTemplate.is_enabled == True,  # noqa: E712
            )
        )
        template = result.scalar_one_or_none()
        if template:
            return template

        # 模糊匹配（包含关键词）
        result = await db.execute(
            select(PositionTemplate).where(
                PositionTemplate.position_tag.ilike(f"%{position_tag}%"),
                PositionTemplate.is_enabled == True,  # noqa: E712
            ).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def increment_usage_count(db: AsyncSession, retrieved_questions: List[dict]):
        """将被检索到的题目 usage_count +1"""
        for item in retrieved_questions:
            question = item.get("instance")
            if question:
                question.usage_count = (question.usage_count or 0) + 1
        await db.flush()


rag_service = RAGService()
