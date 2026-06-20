from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.api.backoffice.deps import get_current_admin
from app.models.admin import Admin
from app.schemas.response import ApiResponse
from app.schemas.knowledge import KnowledgeDocumentToggle, KnowledgeTestRetrieve
from app.services.knowledge_service import knowledge_service

router = APIRouter()


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """文档列表（分页+筛选）"""
    result = await knowledge_service.list_documents(
        db, page, per_page, keyword, category, is_enabled
    )
    return ApiResponse.success(data=result)


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """上传文档"""
    doc = await knowledge_service.upload_document(db, file, title, category, description)
    return ApiResponse.success(data=doc)


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取文档详情"""
    doc = await knowledge_service.get_document_response(db, document_id)
    return ApiResponse.success(data=doc)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除文档"""
    await knowledge_service.delete_document(db, document_id)
    return ApiResponse.success(message="删除成功")


@router.patch("/documents/{document_id}/toggle")
async def toggle_document(
    document_id: int,
    data: KnowledgeDocumentToggle,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """启用/禁用文档"""
    doc = await knowledge_service.toggle_document(db, document_id, data.is_enabled)
    return ApiResponse.success(data=doc)


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """重建文档向量索引"""
    doc = await knowledge_service.reindex_document(db, document_id)
    return ApiResponse.success(data=doc)


@router.get("/documents/{document_id}/chunks")
async def list_chunks(
    document_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取文档分块列表"""
    result = await knowledge_service.list_chunks(db, document_id, page, per_page)
    return ApiResponse.success(data=result)


@router.post("/test-retrieve")
async def test_retrieve(
    data: KnowledgeTestRetrieve,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """知识文档检索测试"""
    results = await knowledge_service.test_retrieve(db, data)
    return ApiResponse.success(data=results)
