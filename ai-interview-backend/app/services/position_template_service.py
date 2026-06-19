import logging
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.position_template import PositionTemplate
from app.schemas.position_template import (
    PositionTemplateCreate, PositionTemplateUpdate, PositionTemplateResponse
)
from app.exceptions.http_exceptions import APIException

logger = logging.getLogger(__name__)


class PositionTemplateService:

    @staticmethod
    async def list_templates(
        db: AsyncSession, page: int = 1, per_page: int = 15, keyword: Optional[str] = None
    ) -> Dict:
        query = select(PositionTemplate)

        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.where(
                (PositionTemplate.title.ilike(like_pattern))
                | (PositionTemplate.position_tag.ilike(like_pattern))
            )

        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()

        # Paginate
        offset = (page - 1) * per_page
        query = query.order_by(PositionTemplate.id.desc()).offset(offset).limit(per_page)
        result = await db.execute(query)
        templates = result.scalars().all()

        items = [PositionTemplateService._to_response(t) for t in templates]

        return {
            "items": items,
            "total": total,
            "per_page": per_page,
            "current_page": page,
        }

    @staticmethod
    async def get_template(db: AsyncSession, id: int) -> PositionTemplate:
        template = await db.get(PositionTemplate, id)
        if not template:
            raise APIException(status_code=404, message="岗位模板不存在")
        return template

    @staticmethod
    async def get_template_response(db: AsyncSession, id: int) -> PositionTemplateResponse:
        template = await PositionTemplateService.get_template(db, id)
        return PositionTemplateService._to_response(template)

    @staticmethod
    async def create_template(db: AsyncSession, data: PositionTemplateCreate) -> PositionTemplateResponse:
        template = PositionTemplate(
            position_tag=data.position_tag,
            title=data.title,
            category=data.category,
            level=data.level,
            description=data.description,
            core_skills=data.core_skills,
            interview_focus=data.interview_focus,
            recommended_difficulty=data.recommended_difficulty,
            recommended_questions=data.recommended_questions,
            key_evaluation_criteria=data.key_evaluation_criteria,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return PositionTemplateService._to_response(template)

    @staticmethod
    async def update_template(
        db: AsyncSession, id: int, data: PositionTemplateUpdate
    ) -> PositionTemplateResponse:
        template = await PositionTemplateService.get_template(db, id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        await db.commit()
        await db.refresh(template)
        return PositionTemplateService._to_response(template)

    @staticmethod
    async def delete_template(db: AsyncSession, id: int) -> None:
        template = await PositionTemplateService.get_template(db, id)
        await db.delete(template)
        await db.commit()

    @staticmethod
    async def toggle_template(db: AsyncSession, id: int, is_enabled: bool) -> PositionTemplateResponse:
        template = await PositionTemplateService.get_template(db, id)
        template.is_enabled = is_enabled
        await db.commit()
        await db.refresh(template)
        return PositionTemplateService._to_response(template)

    # ---- Helpers ----

    @staticmethod
    def _to_response(template: PositionTemplate) -> PositionTemplateResponse:
        return PositionTemplateResponse(
            id=template.id,
            position_tag=template.position_tag,
            title=template.title,
            category=template.category,
            level=template.level,
            description=template.description,
            core_skills=template.core_skills,
            interview_focus=template.interview_focus,
            recommended_difficulty=template.recommended_difficulty,
            recommended_questions=template.recommended_questions,
            key_evaluation_criteria=template.key_evaluation_criteria,
            is_enabled=template.is_enabled,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )


position_template_service = PositionTemplateService()
