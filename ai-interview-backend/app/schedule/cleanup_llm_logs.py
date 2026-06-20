import logging
from datetime import datetime, timedelta, UTC
from sqlalchemy import delete
from app.db.base import create_scheduler_engine, create_scheduler_session_factory
from app.models.llm_call_log import LLMCallLog

logger = logging.getLogger(__name__)

# 默认保留天数
RETENTION_DAYS = 30


async def cleanup_llm_logs():
    """清理超过保留期的 LLM 调用日志"""
    scheduler_engine = create_scheduler_engine()
    SchedulerSessionLocal = create_scheduler_session_factory(scheduler_engine)

    async with SchedulerSessionLocal() as db:
        try:
            cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
            result = await db.execute(
                delete(LLMCallLog).where(LLMCallLog.created_at < cutoff)
            )
            await db.commit()
            deleted = result.rowcount
            if deleted > 0:
                logger.info(f"已清理 {deleted} 条超过 {RETENTION_DAYS} 天的 LLM 调用日志")
        except Exception as e:
            logger.error(f"清理 LLM 日志失败: {e}", exc_info=True)
        finally:
            await scheduler_engine.dispose()
