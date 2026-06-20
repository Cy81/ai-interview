"""
LangChain 模型工厂 - 统一管理 ChatOpenAI 和 OpenAIEmbeddings 实例
60 秒 TTL 缓存，DB 配置 → .env 回退
"""
import time
import asyncio
import logging
from typing import Optional, Tuple

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)

_chat_model: Optional[ChatOpenAI] = None
_embedding_model: Optional[OpenAIEmbeddings] = None
_model_name: Optional[str] = None
_cache_loaded_at: float = 0
_CACHE_TTL = 60
_cache_lock = asyncio.Lock()


async def get_chat_model() -> Tuple[ChatOpenAI, str]:
    """返回 (ChatOpenAI, model_name)，带 60s 缓存"""
    global _chat_model, _model_name, _cache_loaded_at

    now = time.monotonic()
    if _chat_model is not None and (now - _cache_loaded_at) < _CACHE_TTL:
        return _chat_model, _model_name

    async with _cache_lock:
        now = time.monotonic()
        if _chat_model is not None and (now - _cache_loaded_at) < _CACHE_TTL:
            return _chat_model, _model_name

        api_key, base_url, model_name = await _resolve_provider_config()

        _chat_model = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            max_tokens=2000,
            stream_usage=True,
        )
        _model_name = model_name
        _cache_loaded_at = time.monotonic()
        logger.info(f"LangChat ChatModel 已缓存: model={model_name}")
        return _chat_model, _model_name


async def get_embedding_model() -> OpenAIEmbeddings:
    """返回 OpenAIEmbeddings，带 60s 缓存"""
    global _embedding_model, _cache_loaded_at

    now = time.monotonic()
    if _embedding_model is not None and (now - _cache_loaded_at) < _CACHE_TTL:
        return _embedding_model

    async with _cache_lock:
        now = time.monotonic()
        if _embedding_model is not None and (now - _cache_loaded_at) < _CACHE_TTL:
            return _embedding_model

        api_key, base_url, _ = await _resolve_provider_config()

        _embedding_model = OpenAIEmbeddings(
            api_key=api_key,
            base_url=base_url,
            model=getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-small"),
            dimensions=int(getattr(settings, "EMBEDDING_DIM", 1024)),
        )
        _cache_loaded_at = time.monotonic()
        logger.info("LangChain EmbeddingModel 已缓存")
        return _embedding_model


async def invalidate_cache():
    """清除所有缓存，下次调用重新从数据库加载"""
    global _chat_model, _embedding_model, _model_name, _cache_loaded_at
    _chat_model = None
    _embedding_model = None
    _model_name = None
    _cache_loaded_at = 0
    logger.info("LangChain 模型缓存已清除")


async def _resolve_provider_config() -> Tuple[str, str, str]:
    """DB 配置 → .env 回退。返回 (api_key, base_url, model_name)"""
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
                logger.info(f"AI 配置从 DB 加载: provider={provider.name}, model={model.model_name}")
                return provider.api_key, provider.base_url, model.model_name
    except Exception as e:
        logger.error(f"DB 配置加载失败: {e}，回退到 .env")

    logger.warning("无激活 DB 配置，使用 .env 默认值")
    return settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_BASE_URL, settings.DEEPSEEK_MODEL
