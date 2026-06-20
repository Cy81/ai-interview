import logging
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete

from app.models.question_bank import QuestionBank
from app.schemas.question_bank import (
    QuestionBankCreate, QuestionBankUpdate, QuestionBankResponse,
    QuestionBankStats, QuestionBankRetrieveResult,
    QuestionBankBatchImport, QuestionBankTestRetrieve
)
from app.services.embedding_service import embedding_service
from app.exceptions.http_exceptions import APIException

logger = logging.getLogger(__name__)


class QuestionBankService:

    # ---- List & Stats ----

    @staticmethod
    async def list_questions(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        is_enabled: Optional[bool] = None
    ) -> Dict:
        query = select(QuestionBank)

        if keyword:
            query = query.where(QuestionBank.question.ilike(f"%{keyword}%"))
        if category:
            query = query.where(QuestionBank.category == category)
        if difficulty:
            query = query.where(QuestionBank.difficulty == difficulty)
        if is_enabled is not None:
            query = query.where(QuestionBank.is_enabled == is_enabled)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # Paginate
        query = query.order_by(QuestionBank.id.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await db.execute(query)
        questions = result.scalars().all()

        items = [QuestionBankService._to_response(q) for q in questions]

        return {
            "items": items,
            "total": total,
            "per_page": per_page,
            "current_page": page
        }

    @staticmethod
    async def get_stats(db: AsyncSession) -> QuestionBankStats:
        total = await db.scalar(select(func.count(QuestionBank.id)))

        vectorized = await db.scalar(
            select(func.count(QuestionBank.id)).where(QuestionBank.is_vectorized == True)
        )

        categories = await db.scalar(
            select(func.count(func.distinct(QuestionBank.category)))
        )

        max_usage = await db.scalar(select(func.max(QuestionBank.usage_count)))
        if max_usage is None:
            max_usage = 0

        return QuestionBankStats(
            total=total or 0,
            vectorized=vectorized or 0,
            categories=categories or 0,
            max_usage=max_usage
        )

    # ---- Single CRUD ----

    @staticmethod
    async def get_question(db: AsyncSession, id: int) -> QuestionBank:
        question = await db.get(QuestionBank, id)
        if not question:
            raise APIException(status_code=404, message="题目不存在")
        return question

    @staticmethod
    async def get_question_response(db: AsyncSession, id: int) -> QuestionBankResponse:
        question = await QuestionBankService.get_question(db, id)
        return QuestionBankService._to_response(question)

    @staticmethod
    async def create_question(db: AsyncSession, data: QuestionBankCreate) -> QuestionBankResponse:
        question = QuestionBank(
            category=data.category,
            position_tag=data.position_tag,
            difficulty=data.difficulty,
            question=data.question,
            reference_answer=data.reference_answer,
            key_points=data.key_points,
            tags=data.tags
        )
        db.add(question)

        # Generate embedding
        embedding = await embedding_service.get_embedding(data.question)
        if embedding is not None:
            question.embedding = embedding
            question.is_vectorized = True

        await db.commit()
        await db.refresh(question)
        return QuestionBankService._to_response(question)

    @staticmethod
    async def update_question(db: AsyncSession, id: int, data: QuestionBankUpdate) -> QuestionBankResponse:
        question = await QuestionBankService.get_question(db, id)

        update_data = data.model_dump(exclude_unset=True)

        question_text_changed = "question" in update_data
        for field, value in update_data.items():
            setattr(question, field, value)

        # Regenerate embedding if question text changed
        if question_text_changed:
            embedding = await embedding_service.get_embedding(question.question)
            if embedding is not None:
                question.embedding = embedding
                question.is_vectorized = True
            else:
                question.is_vectorized = False

        await db.commit()
        await db.refresh(question)
        return QuestionBankService._to_response(question)

    @staticmethod
    async def delete_question(db: AsyncSession, id: int) -> None:
        question = await QuestionBankService.get_question(db, id)
        await db.delete(question)
        await db.commit()

    @staticmethod
    async def toggle_question(db: AsyncSession, id: int, is_enabled: bool) -> QuestionBankResponse:
        question = await QuestionBankService.get_question(db, id)
        question.is_enabled = is_enabled
        await db.commit()
        await db.refresh(question)
        return QuestionBankService._to_response(question)

    # ---- Batch Operations ----

    @staticmethod
    async def batch_import(db: AsyncSession, data: QuestionBankBatchImport) -> Dict:
        questions = []
        texts = []

        for item in data.questions:
            question = QuestionBank(
                category=item.category,
                position_tag=item.position_tag,
                difficulty=item.difficulty,
                question=item.question,
                reference_answer=item.reference_answer,
                key_points=item.key_points,
                tags=item.tags
            )
            db.add(question)
            questions.append(question)
            texts.append(item.question)

        # Batch generate embeddings
        embeddings = await embedding_service.get_embeddings_batch(texts)

        vectorized_count = 0
        for question, emb in zip(questions, embeddings):
            if emb is not None:
                question.embedding = emb
                question.is_vectorized = True
                vectorized_count += 1

        await db.commit()

        return {
            "imported": len(questions),
            "vectorized": vectorized_count
        }

    @staticmethod
    async def reindex_all(db: AsyncSession) -> Dict:
        result = await db.execute(select(QuestionBank))
        all_questions = result.scalars().all()

        # Collect questions that need re-embedding
        to_embed = [q for q in all_questions if q.question]
        texts = [q.question for q in to_embed]

        if not texts:
            return {"total": len(all_questions), "vectorized": 0}

        embeddings = await embedding_service.get_embeddings_batch(texts)

        vectorized_count = 0
        for question, emb in zip(to_embed, embeddings):
            if emb is not None:
                question.embedding = emb
                question.is_vectorized = True
                vectorized_count += 1

        await db.commit()

        return {
            "total": len(all_questions),
            "vectorized": vectorized_count
        }

    # ---- Vector Retrieval ----

    @staticmethod
    async def test_retrieve(db: AsyncSession, data: QuestionBankTestRetrieve) -> List[QuestionBankRetrieveResult]:
        query_embedding = await embedding_service.get_embedding(data.query)
        if query_embedding is None:
            raise APIException(status_code=500, message="生成查询向量失败")

        # Build filters
        filters = [QuestionBank.is_enabled == True]
        if data.position_tag:
            filters.append(QuestionBank.position_tag == data.position_tag)
        if data.difficulty:
            filters.append(QuestionBank.difficulty == data.difficulty)

        results = await embedding_service.vector_search(
            db=db,
            model_class=QuestionBank,
            query_embedding=query_embedding,
            filters=filters,
            top_k=data.top_k,
            min_score=data.min_score or 0.0
        )

        return [
            QuestionBankRetrieveResult(
                similarity_score=row["similarity_score"],
                question_id=row["instance"].id,
                question=row["instance"].question,
                category=row["instance"].category,
                difficulty=row["instance"].difficulty,
                position_tag=row["instance"].position_tag,
                reference_answer=row["instance"].reference_answer
            )
            for row in results
        ]

    # ---- Helpers ----

    @staticmethod
    def _to_response(question: QuestionBank) -> QuestionBankResponse:
        return QuestionBankResponse(
            id=question.id,
            category=question.category,
            position_tag=question.position_tag,
            difficulty=question.difficulty,
            question=question.question,
            reference_answer=question.reference_answer,
            key_points=question.key_points,
            tags=question.tags,
            is_vectorized=question.is_vectorized,
            usage_count=question.usage_count,
            is_enabled=question.is_enabled,
            created_at=question.created_at,
            updated_at=question.updated_at
        )


question_bank_service = QuestionBankService()
