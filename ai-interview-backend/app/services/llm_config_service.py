import time
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from openai import AsyncOpenAI

from app.models.llm_provider import LLMProvider, LLMModel
from app.schemas.llm_config import (
    LLMProviderCreate, LLMProviderUpdate,
    LLMModelCreate, LLMModelUpdate,
    LLMConfigTestRequest, LLMConfigTestResponse,
    LLMProviderResponse, LLMModelResponse, mask_api_key
)
from app.exceptions.http_exceptions import APIException

logger = logging.getLogger(__name__)


class LLMConfigService:

    # ---- Provider CRUD ----

    @staticmethod
    async def list_providers(db: AsyncSession) -> List[LLMProviderResponse]:
        query = select(LLMProvider).order_by(LLMProvider.id)
        result = await db.execute(query)
        providers = result.scalars().all()
        return [LLMConfigService._provider_to_response(p) for p in providers]

    @staticmethod
    async def get_provider(db: AsyncSession, provider_id: int) -> LLMProvider:
        provider = await db.get(LLMProvider, provider_id)
        if not provider:
            raise APIException(status_code=404, message="提供商不存在")
        return provider

    @staticmethod
    async def create_provider(db: AsyncSession, data: LLMProviderCreate) -> LLMProviderResponse:
        existing = await db.scalar(select(LLMProvider).where(LLMProvider.name == data.name))
        if existing:
            raise APIException(status_code=400, message=f"提供商名称 '{data.name}' 已存在")

        provider = LLMProvider(
            name=data.name,
            base_url=data.base_url,
            api_key=data.api_key,
            is_enabled=True
        )
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
        return LLMConfigService._provider_to_response(provider)

    @staticmethod
    async def update_provider(db: AsyncSession, provider_id: int, data: LLMProviderUpdate) -> LLMProviderResponse:
        provider = await LLMConfigService.get_provider(db, provider_id)

        if data.name is not None:
            existing = await db.scalar(
                select(LLMProvider).where(LLMProvider.name == data.name, LLMProvider.id != provider_id)
            )
            if existing:
                raise APIException(status_code=400, message=f"提供商名称 '{data.name}' 已存在")
            provider.name = data.name
        if data.base_url is not None:
            provider.base_url = data.base_url
        if data.api_key is not None:
            provider.api_key = data.api_key
        if data.is_enabled is not None:
            provider.is_enabled = data.is_enabled

        await db.commit()
        await db.refresh(provider)

        from app.services.client.ai_service import AIService
        await AIService.invalidate_config_cache()

        return LLMConfigService._provider_to_response(provider)

    @staticmethod
    async def delete_provider(db: AsyncSession, provider_id: int) -> None:
        provider = await LLMConfigService.get_provider(db, provider_id)

        active_model = await db.scalar(
            select(LLMModel).where(LLMModel.provider_id == provider_id, LLMModel.is_active == True)
        )
        if active_model:
            raise APIException(status_code=400, message="不能删除包含激活模型的提供商，请先切换到其他模型")

        await db.delete(provider)
        await db.commit()

    # ---- Model CRUD ----

    @staticmethod
    async def add_model(db: AsyncSession, provider_id: int, data: LLMModelCreate) -> LLMModelResponse:
        await LLMConfigService.get_provider(db, provider_id)

        existing = await db.scalar(
            select(LLMModel).where(
                LLMModel.provider_id == provider_id,
                LLMModel.model_name == data.model_name
            )
        )
        if existing:
            raise APIException(status_code=400, message=f"模型 '{data.model_name}' 已存在")

        model = LLMModel(
            provider_id=provider_id,
            model_name=data.model_name,
            display_name=data.display_name,
            is_active=False
        )
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return LLMConfigService._model_to_response(model)

    @staticmethod
    async def update_model(db: AsyncSession, model_id: int, data: LLMModelUpdate) -> LLMModelResponse:
        model = await db.get(LLMModel, model_id)
        if not model:
            raise APIException(status_code=404, message="模型不存在")

        if data.model_name is not None:
            existing = await db.scalar(
                select(LLMModel).where(
                    LLMModel.provider_id == model.provider_id,
                    LLMModel.model_name == data.model_name,
                    LLMModel.id != model_id
                )
            )
            if existing:
                raise APIException(status_code=400, message=f"模型 '{data.model_name}' 已存在")
            model.model_name = data.model_name
        if data.display_name is not None:
            model.display_name = data.display_name

        await db.commit()
        await db.refresh(model)

        from app.services.client.ai_service import AIService
        await AIService.invalidate_config_cache()

        return LLMConfigService._model_to_response(model)

    @staticmethod
    async def delete_model(db: AsyncSession, model_id: int) -> None:
        model = await db.get(LLMModel, model_id)
        if not model:
            raise APIException(status_code=404, message="模型不存在")
        if model.is_active:
            raise APIException(status_code=400, message="不能删除当前激活的模型，请先切换到其他模型")

        await db.delete(model)
        await db.commit()

    @staticmethod
    async def set_active_model(db: AsyncSession, model_id: int) -> LLMModelResponse:
        model = await db.get(LLMModel, model_id)
        if not model:
            raise APIException(status_code=404, message="模型不存在")

        provider = await db.get(LLMProvider, model.provider_id)
        if not provider or not provider.is_enabled:
            raise APIException(status_code=400, message="该模型所属的提供商未启用")

        await db.execute(update(LLMModel).values(is_active=False))
        model.is_active = True
        await db.commit()
        await db.refresh(model)

        from app.services.client.ai_service import AIService
        await AIService.invalidate_config_cache()

        return LLMConfigService._model_to_response(model)

    # ---- Test ----

    @staticmethod
    async def test_config(data: LLMConfigTestRequest, db: AsyncSession = None) -> LLMConfigTestResponse:
        api_key = data.api_key
        base_url = data.base_url

        # 如果提供了 provider_id，从数据库获取真实的 API Key
        if data.provider_id and db:
            provider = await db.get(LLMProvider, data.provider_id)
            if provider:
                api_key = provider.api_key
                base_url = provider.base_url

        test_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        start = time.monotonic()
        try:
            response = await test_client.chat.completions.create(
                model=data.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            model_returned = response.model if hasattr(response, "model") else None
            return LLMConfigTestResponse(
                success=True,
                latency_ms=latency_ms,
                model_returned=model_returned
            )
        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            error_msg = str(e)
            if len(error_msg) > 500:
                error_msg = error_msg[:500] + "..."
            return LLMConfigTestResponse(
                success=False,
                latency_ms=latency_ms,
                error=error_msg
            )
        finally:
            await test_client.close()

    # ---- Helpers ----

    @staticmethod
    def _provider_to_response(provider: LLMProvider) -> LLMProviderResponse:
        models = [LLMConfigService._model_to_response(m) for m in (provider.models or [])]
        return LLMProviderResponse(
            id=provider.id,
            name=provider.name,
            base_url=provider.base_url,
            api_key_masked=mask_api_key(provider.api_key),
            is_enabled=provider.is_enabled,
            models=models,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    @staticmethod
    def _model_to_response(model: LLMModel) -> LLMModelResponse:
        return LLMModelResponse(
            id=model.id,
            provider_id=model.provider_id,
            model_name=model.model_name,
            display_name=model.display_name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


llm_config_service = LLMConfigService()
