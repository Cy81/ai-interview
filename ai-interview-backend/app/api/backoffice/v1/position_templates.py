from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.api.backoffice.deps import get_current_admin
from app.models.admin import Admin
from app.schemas.response import ApiResponse
from app.schemas.position_template import (
    PositionTemplateCreate, PositionTemplateUpdate, PositionTemplateToggle
)
from app.services.position_template_service import position_template_service

router = APIRouter()


@router.get("")
async def list_templates(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """岗位模板列表"""
    result = await position_template_service.list_templates(db, page, per_page, keyword)
    return ApiResponse.success(data=result)


@router.post("")
async def create_template(
    data: PositionTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """创建岗位模板"""
    template = await position_template_service.create_template(db, data)
    return ApiResponse.success(data=template)


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取岗位模板详情"""
    template = await position_template_service.get_template_response(db, template_id)
    return ApiResponse.success(data=template)


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    data: PositionTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新岗位模板"""
    template = await position_template_service.update_template(db, template_id, data)
    return ApiResponse.success(data=template)


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除岗位模板"""
    await position_template_service.delete_template(db, template_id)
    return ApiResponse.success(message="删除成功")


@router.patch("/{template_id}/toggle")
async def toggle_template(
    template_id: int,
    data: PositionTemplateToggle,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """启用/禁用岗位模板"""
    template = await position_template_service.toggle_template(db, template_id, data.is_enabled)
    return ApiResponse.success(data=template)
