from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.response import ApiResponse
from app.models.position_template import PositionTemplate

router = APIRouter()


@router.get("")
async def list_position_templates(
    db: AsyncSession = Depends(get_db)
):
    """获取所有启用的岗位模板（供用户选择）"""
    result = await db.execute(
        select(PositionTemplate).where(
            PositionTemplate.is_enabled == True  # noqa: E712
        ).order_by(PositionTemplate.position_tag)
    )
    templates = result.scalars().all()

    items = [
        {
            "id": t.id,
            "position_tag": t.position_tag,
            "core_skills": t.core_skills or [],
            "interview_focus": t.interview_focus,
            "key_evaluation_criteria": t.key_evaluation_criteria,
        }
        for t in templates
    ]
    return ApiResponse.success(data=items)
