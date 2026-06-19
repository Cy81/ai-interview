from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.api.backoffice.deps import get_current_admin
from app.models.admin import Admin
from app.schemas.response import ApiResponse
from app.schemas.question_bank import (
    QuestionBankCreate, QuestionBankUpdate,
    QuestionBankBatchImport, QuestionBankToggle,
    QuestionBankTestRetrieve
)
from app.services.question_bank_service import question_bank_service

router = APIRouter()


@router.get("")
async def list_questions(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """题库列表（分页+筛选）"""
    result = await question_bank_service.list_questions(
        db, page, per_page, keyword, category, difficulty, is_enabled
    )
    return ApiResponse.success(data=result)


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """题库统计"""
    stats = await question_bank_service.get_stats(db)
    return ApiResponse.success(data=stats)


@router.post("")
async def create_question(
    data: QuestionBankCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """创建题目"""
    question = await question_bank_service.create_question(db, data)
    return ApiResponse.success(data=question)


@router.get("/{question_id}")
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取题目详情"""
    question = await question_bank_service.get_question_response(db, question_id)
    return ApiResponse.success(data=question)


@router.put("/{question_id}")
async def update_question(
    question_id: int,
    data: QuestionBankUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新题目"""
    question = await question_bank_service.update_question(db, question_id, data)
    return ApiResponse.success(data=question)


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除题目"""
    await question_bank_service.delete_question(db, question_id)
    return ApiResponse.success(message="删除成功")


@router.patch("/{question_id}/toggle")
async def toggle_question(
    question_id: int,
    data: QuestionBankToggle,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """启用/禁用题目"""
    question = await question_bank_service.toggle_question(db, question_id, data.is_enabled)
    return ApiResponse.success(data=question)


@router.post("/batch-import")
async def batch_import(
    data: QuestionBankBatchImport,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """批量导入题目"""
    result = await question_bank_service.batch_import(db, data)
    return ApiResponse.success(data=result)


@router.post("/reindex-all")
async def reindex_all(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """全量重建向量索引"""
    result = await question_bank_service.reindex_all(db)
    return ApiResponse.success(data=result)


@router.post("/test-retrieve")
async def test_retrieve(
    data: QuestionBankTestRetrieve,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """题库检索测试"""
    results = await question_bank_service.test_retrieve(db, data)
    return ApiResponse.success(data=results)
