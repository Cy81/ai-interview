import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.llm_config_cache import get_llm_client, get_embedding_model_name, invalidate_cache as _invalidate_cache

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_DIM = 1024


class EmbeddingService:

    @staticmethod
    async def _get_client() -> tuple:
        """获取 embedding 客户端和模型名（委托给共享缓存模块）"""
        client, _ = await get_llm_client()
        model_name = await get_embedding_model_name()
        return client, model_name

    @staticmethod
    async def invalidate_cache():
        """清除缓存"""
        await _invalidate_cache()

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
