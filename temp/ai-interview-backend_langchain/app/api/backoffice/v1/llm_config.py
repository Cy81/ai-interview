from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.backoffice.deps import get_current_admin
from app.models.admin import Admin
from app.schemas.response import ApiResponse
from app.schemas.llm_config import (
    LLMProviderCreate, LLMProviderUpdate,
    LLMModelCreate, LLMModelUpdate,
    LLMConfigTestRequest
)
from app.services.llm_config_service import llm_config_service

router = APIRouter()


# ---- Provider Endpoints ----

@router.get("")
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取所有 LLM 提供商列表（含模型）"""
    providers = await llm_config_service.list_providers(db)
    return ApiResponse.success(data=providers)


@router.post("")
async def create_provider(
    data: LLMProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """创建 LLM 提供商"""
    provider = await llm_config_service.create_provider(db, data)
    return ApiResponse.success(data=provider)


@router.put("/{provider_id}")
async def update_provider(
    provider_id: int,
    data: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新 LLM 提供商"""
    provider = await llm_config_service.update_provider(db, provider_id, data)
    return ApiResponse.success(data=provider)


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除 LLM 提供商"""
    await llm_config_service.delete_provider(db, provider_id)
    return ApiResponse.success(message="删除成功")


# ---- Model Endpoints ----

@router.post("/{provider_id}/models")
async def add_model(
    provider_id: int,
    data: LLMModelCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """为提供商添加模型"""
    model = await llm_config_service.add_model(db, provider_id, data)
    return ApiResponse.success(data=model)


@router.put("/models/{model_id}")
async def update_model(
    model_id: int,
    data: LLMModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新模型"""
    model = await llm_config_service.update_model(db, model_id, data)
    return ApiResponse.success(data=model)


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除模型"""
    await llm_config_service.delete_model(db, model_id)
    return ApiResponse.success(message="删除成功")


@router.put("/models/{model_id}/activate")
async def activate_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """激活模型（全局唯一）"""
    model = await llm_config_service.set_active_model(db, model_id)
    return ApiResponse.success(data=model)


# ---- Test Endpoint ----

@router.post("/test")
async def test_config(
    data: LLMConfigTestRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """测试 LLM 配置可用性"""
    result = await llm_config_service.test_config(data, db)
    return ApiResponse.success(data=result)
