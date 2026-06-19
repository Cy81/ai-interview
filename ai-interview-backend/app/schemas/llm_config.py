from .base import BaseSchema
from typing import Optional, List
from datetime import datetime


# ---- Provider Schemas ----

class LLMProviderCreate(BaseSchema):
    name: str
    base_url: str
    api_key: str


class LLMProviderUpdate(BaseSchema):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: Optional[bool] = None


class LLMModelResponse(BaseSchema):
    id: int
    provider_id: int
    model_name: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LLMProviderResponse(BaseSchema):
    id: int
    name: str
    base_url: str
    api_key_masked: str
    is_enabled: bool
    models: List[LLMModelResponse] = []
    created_at: datetime
    updated_at: datetime


# ---- Model Schemas ----

class LLMModelCreate(BaseSchema):
    model_name: str
    display_name: str


class LLMModelUpdate(BaseSchema):
    model_name: Optional[str] = None
    display_name: Optional[str] = None


# ---- Test Schemas ----

class LLMConfigTestRequest(BaseSchema):
    base_url: str
    api_key: str
    model_name: str
    provider_id: Optional[int] = None  # 如提供，使用数据库中存储的 API Key


class LLMConfigTestResponse(BaseSchema):
    success: bool
    latency_ms: Optional[int] = None
    model_returned: Optional[str] = None
    error: Optional[str] = None


def mask_api_key(key: str) -> str:
    """掩码处理 API Key，仅显示前4位和后4位"""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"
