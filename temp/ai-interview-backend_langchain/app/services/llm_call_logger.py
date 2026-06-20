import asyncio
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# 防止 asyncio.create_task 的任务被 GC（Python 3.12+）
_background_tasks: set = set()


async def _write_log(
    interview_id: Optional[int],
    call_type: str,
    question_index: Optional[int],
    model_name: str,
    temperature: float,
    request_messages: list,
    response_content: Optional[str],
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: int,
    status: str,
    error_message: Optional[str],
    extra_metadata: Optional[dict],
):
    try:
        from app.db.session import async_session
        from app.models.llm_call_log import LLMCallLog

        async with async_session() as db:
            log_entry = LLMCallLog(
                interview_id=interview_id,
                call_type=call_type,
                question_index=question_index,
                model_name=model_name,
                temperature=temperature,
                request_messages=request_messages,
                response_content=response_content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                status=status,
                error_message=error_message,
                extra_metadata=extra_metadata,
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        logger.error(f"写入 LLM 调用日志失败: {e}")


def log_llm_call(
    interview_id: Optional[int],
    call_type: str,
    question_index: Optional[int],
    model_name: str,
    temperature: float,
    request_messages: list,
    response_content: Optional[str],
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    latency_ms: int = 0,
    status: str = "success",
    error_message: Optional[str] = None,
    extra_metadata: Optional[dict] = None,
):
    """Fire-and-forget: 调度异步 DB 写入，不阻塞调用方"""
    task = asyncio.create_task(
        _write_log(
            interview_id=interview_id,
            call_type=call_type,
            question_index=question_index,
            model_name=model_name,
            temperature=temperature,
            request_messages=request_messages,
            response_content=response_content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            extra_metadata=extra_metadata,
        )
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
