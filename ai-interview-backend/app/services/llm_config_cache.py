"""
共享的 LLM 配置缓存模块。
ai_service 和 embedding_service 共用同一份 provider 配置缓存，
避免重复查询数据库和重复创建客户端实例。
"""
import time
import asyncio
import logging
from typing import Optional, Tuple
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None
_model_name: Optional[str] = None
_loaded_at: float = 0
_lock = asyncio.Lock()
_TTL = 60  # 秒

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


async def get_llm_client() -> Tuple[AsyncOpenAI, str]:
    """获取 LLM 客户端和 chat 模型名，60s TTL 缓存"""
    global _client, _model_name, _loaded_at

    now = time.monotonic()
    if _client is not None and (now - _loaded_at) < _TTL:
        return _client, _model_name

    async with _lock:
        now = time.monotonic()
        if _client is not None and (now - _loaded_at) < _TTL:
            return _client, _model_name

        try:
            from sqlalchemy import select
            from app.models.llm_provider import LLMProvider, LLMModel
            from app.db.session import async_session

            async with async_session() as db:
                result = await db.execute(
                    select(LLMModel)
                    .join(LLMProvider)
                    .where(LLMModel.is_active == True, LLMProvider.is_enabled == True)
                )
                model = result.scalar_one_or_none()

                if model is not None:
                    provider = await db.get(LLMProvider, model.provider_id)
                    _client = AsyncOpenAI(
                        api_key=provider.api_key,
                        base_url=provider.base_url,
                        timeout=60
                    )
                    _model_name = model.model_name
                    logger.info(f"LLM 配置已从数据库加载: provider={provider.name}, model={model.model_name}")
                else:
                    _client = AsyncOpenAI(
                        api_key=settings.DEEPSEEK_API_KEY,
                        base_url=settings.DEEPSEEK_BASE_URL,
                        timeout=60
                    )
                    _model_name = settings.DEEPSEEK_MODEL
                    logger.warning("数据库中没有激活的 LLM 配置，使用 .env 默认配置")
        except Exception as e:
            logger.error(f"从数据库加载 LLM 配置失败: {e}，回退到 .env 默认配置")
            _client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                timeout=60
            )
            _model_name = settings.DEEPSEEK_MODEL

        _loaded_at = time.monotonic()
        return _client, _model_name


async def get_embedding_model_name() -> str:
    """获取 embedding 模型名（不缓存，直接读配置）"""
    return getattr(settings, 'EMBEDDING_MODEL', DEFAULT_EMBEDDING_MODEL)


async def invalidate_cache():
    """清除缓存（LLM 配置变更后调用）"""
    global _client, _model_name, _loaded_at
    _client = None
    _model_name = None
    _loaded_at = 0
    logger.info("LLM 配置缓存已清除")
