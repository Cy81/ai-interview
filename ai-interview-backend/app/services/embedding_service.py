import logging
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Embedding 配置缓存
_embedding_client: Optional[AsyncOpenAI] = None
_embedding_model: Optional[str] = None
_cache_loaded_at: float = 0
_CACHE_TTL = 60

# 默认 embedding 模型
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIM = 1024


class EmbeddingService:

    @staticmethod
    async def _get_client() -> tuple:
        """获取 embedding 客户端和模型名，复用 AIService 的 provider 配置"""
        global _embedding_client, _embedding_model, _cache_loaded_at
        import time

        now = time.monotonic()
        if _embedding_client is not None and (now - _cache_loaded_at) < _CACHE_TTL:
            return _embedding_client, _embedding_model

        try:
            # 尝试从数据库获取 provider 配置（复用 chat 模型的 provider）
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
                    _embedding_client = AsyncOpenAI(
                        api_key=provider.api_key,
                        base_url=provider.base_url
                    )
                else:
                    _embedding_client = AsyncOpenAI(
                        api_key=settings.DEEPSEEK_API_KEY,
                        base_url=settings.DEEPSEEK_BASE_URL
                    )
        except Exception as e:
            logger.warning(f"从数据库加载 embedding 配置失败: {e}，使用 .env 默认配置")
            _embedding_client = AsyncOpenAI(
                api_key=getattr(settings, 'DEEPSEEK_API_KEY', ''),
                base_url=getattr(settings, 'DEEPSEEK_BASE_URL', '')
            )

        # embedding 模型使用环境变量或默认值
        _embedding_model = getattr(settings, 'EMBEDDING_MODEL', DEFAULT_EMBEDDING_MODEL)
        _cache_loaded_at = time.monotonic()
        return _embedding_client, _embedding_model

    @staticmethod
    async def invalidate_cache():
        """清除缓存"""
        global _embedding_client, _embedding_model, _cache_loaded_at
        _embedding_client = None
        _embedding_model = None
        _cache_loaded_at = 0

    @staticmethod
    def _get_dim() -> int:
        """获取 embedding 维度配置"""
        return int(getattr(settings, 'EMBEDDING_DIM', DEFAULT_EMBEDDING_DIM))

    @staticmethod
    async def get_embedding(text: str) -> Optional[List[float]]:
        """生成单条文本的 embedding 向量"""
        try:
            client, model_name = await EmbeddingService._get_client()
            response = await client.embeddings.create(
                model=model_name,
                input=text,
                dimensions=EmbeddingService._get_dim()
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"生成 embedding 失败: {e}")
            return None

    @staticmethod
    async def get_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
        """批量生成 embeddings，每次最多 100 条"""
        results = []
        batch_size = 10

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                client, model_name = await EmbeddingService._get_client()
                response = await client.embeddings.create(
                    model=model_name,
                    input=batch,
                    dimensions=EmbeddingService._get_dim()
                )
                batch_embeddings = [d.embedding for d in response.data]
                results.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"批量 embedding 失败 (batch {i}): {e}")
                results.extend([None] * len(batch))

        return results

    @staticmethod
    async def vector_search(
        db: AsyncSession,
        model_class,
        query_embedding: List[float],
        filters: Optional[List] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        pgvector 余弦相似度检索

        Args:
            db: 数据库会话
            model_class: SQLAlchemy model（需有 embedding 列）
            query_embedding: 查询向量
            filters: 额外的 SQLAlchemy 过滤条件列表
            top_k: 返回数量
            min_score: 最低相似度 (0-1)

        Returns:
            List of dict with 'instance' and 'similarity_score'
        """
        # 计算余弦距离，1 - distance = similarity
        distance_expr = model_class.embedding.cosine_distance(query_embedding)
        similarity_expr = (1 - distance_expr).label("similarity_score")

        query = (
            select(model_class, similarity_expr)
            .where(model_class.embedding.isnot(None))
        )

        # 应用额外过滤条件
        if filters:
            query = query.where(and_(*filters))

        # 按相似度降序排列
        query = query.order_by(distance_expr).limit(top_k)

        result = await db.execute(query)
        rows = result.all()

        results = []
        for row in rows:
            instance = row[0]
            score = float(row[1])
            if score >= min_score:
                results.append({
                    "instance": instance,
                    "similarity_score": round(score, 4)
                })

        return results


embedding_service = EmbeddingService()
