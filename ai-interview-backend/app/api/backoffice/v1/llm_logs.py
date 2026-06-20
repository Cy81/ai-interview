import re
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from typing import Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.api.backoffice.deps import get_current_admin
from app.models.admin import Admin
from app.models.llm_call_log import LLMCallLog
from app.schemas.response import ApiResponse
from app.schemas.paginator import Paginator

router = APIRouter()

# 模型定价表 (每 1K tokens，美元)
MODEL_PRICING = {
    "deepseek-chat": {"input": 0.001, "output": 0.002},
    "deepseek-reasoner": {"input": 0.004, "output": 0.008},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    interview_id: Optional[int] = None,
    call_type: Optional[str] = None,
    model_name: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """获取 LLM 调用日志列表"""
    query = select(LLMCallLog).order_by(LLMCallLog.created_at.desc())

    if interview_id is not None:
        query = query.where(LLMCallLog.interview_id == interview_id)
    if call_type:
        query = query.where(LLMCallLog.call_type == call_type)
    if model_name:
        query = query.where(LLMCallLog.model_name == model_name)
    if status:
        query = query.where(LLMCallLog.status == status)
    if date_from:
        query = query.where(LLMCallLog.created_at >= date_from)
    if date_to:
        query = query.where(LLMCallLog.created_at <= date_to + " 23:59:59")

    paginator = Paginator(query, db)
    result = await paginator.paginate(page, per_page)

    # 截断 response_content 以节省带宽
    def truncate_content(items):
        for item in items:
            if item.response_content and len(item.response_content) > 200:
                item.response_content = item.response_content[:200] + "..."
        return items

    result.process(truncate_content)
    return result.response()


@router.get("/stats")
async def get_stats(
    period: str = Query("day", regex="^(day|week|month)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    model_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """获取 Token 使用统计"""
    query = select(LLMCallLog).where(LLMCallLog.status == "success")

    if date_from:
        query = query.where(LLMCallLog.created_at >= date_from)
    if date_to:
        query = query.where(LLMCallLog.created_at <= date_to + " 23:59:59")
    if model_name:
        query = query.where(LLMCallLog.model_name == model_name)

    # 总计
    total_query = select(
        func.sum(LLMCallLog.prompt_tokens).label("total_prompt"),
        func.sum(LLMCallLog.completion_tokens).label("total_completion"),
        func.sum(LLMCallLog.total_tokens).label("total_tokens"),
        func.count(LLMCallLog.id).label("total_calls"),
        func.avg(LLMCallLog.latency_ms).label("avg_latency"),
    ).select_from(query.subquery())

    total_result = await db.execute(total_query)
    row = total_result.one()

    # 按模型分组
    model_query = select(
        LLMCallLog.model_name,
        func.sum(LLMCallLog.total_tokens).label("total_tokens"),
        func.count(LLMCallLog.id).label("call_count"),
    ).select_from(query.subquery()).group_by(LLMCallLog.model_name)

    model_result = await db.execute(model_query)
    by_model = [
        {"model_name": r.model_name, "total_tokens": r.total_tokens or 0, "call_count": r.call_count}
        for r in model_result.all()
    ]

    # 按调用类型分组
    type_query = select(
        LLMCallLog.call_type,
        func.sum(LLMCallLog.total_tokens).label("total_tokens"),
        func.count(LLMCallLog.id).label("call_count"),
    ).select_from(query.subquery()).group_by(LLMCallLog.call_type)

    type_result = await db.execute(type_query)
    by_call_type = [
        {"call_type": r.call_type, "total_tokens": r.total_tokens or 0, "call_count": r.call_count}
        for r in type_result.all()
    ]

    # 按日分组
    daily_query = select(
        cast(LLMCallLog.created_at, Date).label("date"),
        func.sum(LLMCallLog.total_tokens).label("total_tokens"),
        func.count(LLMCallLog.id).label("call_count"),
    ).select_from(query.subquery()).group_by(cast(LLMCallLog.created_at, Date)).order_by(cast(LLMCallLog.created_at, Date))

    daily_result = await db.execute(daily_query)
    daily_breakdown = [
        {"date": str(r.date), "total_tokens": r.total_tokens or 0, "call_count": r.call_count}
        for r in daily_result.all()
    ]

    return ApiResponse.success(data={
        "total_tokens": row.total_tokens or 0,
        "total_prompt_tokens": row.total_prompt or 0,
        "total_completion_tokens": row.total_completion or 0,
        "total_calls": row.total_calls or 0,
        "avg_latency_ms": int(row.avg_latency or 0),
        "by_model": by_model,
        "by_call_type": by_call_type,
        "daily_breakdown": daily_breakdown,
    })


@router.get("/cost-estimate")
async def get_cost_estimate(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    model_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """获取成本估算"""
    query = select(LLMCallLog).where(LLMCallLog.status == "success")

    if date_from:
        query = query.where(LLMCallLog.created_at >= date_from)
    if date_to:
        query = query.where(LLMCallLog.created_at <= date_to + " 23:59:59")
    if model_name:
        query = query.where(LLMCallLog.model_name == model_name)

    cost_query = select(
        LLMCallLog.model_name,
        func.sum(LLMCallLog.prompt_tokens).label("prompt_tokens"),
        func.sum(LLMCallLog.completion_tokens).label("completion_tokens"),
    ).select_from(query.subquery()).group_by(LLMCallLog.model_name)

    cost_result = await db.execute(cost_query)
    total_cost = 0.0
    by_model = []

    for r in cost_result.all():
        pricing = MODEL_PRICING.get(r.model_name)
        if pricing:
            cost = (r.prompt_tokens or 0) / 1000 * pricing["input"] + \
                   (r.completion_tokens or 0) / 1000 * pricing["output"]
        else:
            cost = 0.0
        total_cost += cost
        by_model.append({
            "model_name": r.model_name,
            "prompt_tokens": r.prompt_tokens or 0,
            "completion_tokens": r.completion_tokens or 0,
            "estimated_cost": round(cost, 4),
            "pricing_available": pricing is not None,
        })

    return ApiResponse.success(data={
        "total_cost": round(total_cost, 4),
        "by_model": by_model,
    })


@router.get("/evaluation")
async def get_evaluation_metrics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    model_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """获取评测指标"""
    # 从 interview_messages 获取评分数据（更可靠）
    from app.models.interview_message import InterviewMessage
    from app.models.interview import Interview

    query = select(
        func.avg(InterviewMessage.score).label("avg_score"),
        func.count(InterviewMessage.id).label("total"),
    ).where(
        InterviewMessage.role == "candidate",
        InterviewMessage.score.isnot(None)
    )

    if date_from:
        query = query.where(InterviewMessage.created_at >= date_from)
    if date_to:
        query = query.where(InterviewMessage.created_at <= date_to + " 23:59:59")

    result = await db.execute(query)
    row = result.one()

    # 分数分布
    distribution = {"1-2": 0, "3-4": 0, "5-6": 0, "7-8": 0, "9-10": 0}
    dist_query = select(InterviewMessage.score).where(
        InterviewMessage.role == "candidate",
        InterviewMessage.score.isnot(None)
    )
    if date_from:
        dist_query = dist_query.where(InterviewMessage.created_at >= date_from)
    if date_to:
        dist_query = dist_query.where(InterviewMessage.created_at <= date_to + " 23:59:59")

    dist_result = await db.execute(dist_query)
    for (score,) in dist_result.all():
        s = float(score)
        if s <= 2:
            distribution["1-2"] += 1
        elif s <= 4:
            distribution["3-4"] += 1
        elif s <= 6:
            distribution["5-6"] += 1
        elif s <= 8:
            distribution["7-8"] += 1
        else:
            distribution["9-10"] += 1

    return ApiResponse.success(data={
        "avg_score": round(float(row.avg_score or 0), 2),
        "total_evaluations": row.total or 0,
        "score_distribution": distribution,
    })


@router.get("/{log_id}")
async def get_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """获取单条日志详情"""
    log = await db.get(LLMCallLog, log_id)
    if not log:
        return ApiResponse.error(message="日志不存在")

    return ApiResponse.success(data={
        "id": log.id,
        "interview_id": log.interview_id,
        "call_type": log.call_type,
        "question_index": log.question_index,
        "model_name": log.model_name,
        "temperature": log.temperature,
        "request_messages": log.request_messages,
        "response_content": log.response_content,
        "prompt_tokens": log.prompt_tokens,
        "completion_tokens": log.completion_tokens,
        "total_tokens": log.total_tokens,
        "latency_ms": log.latency_ms,
        "status": log.status,
        "error_message": log.error_message,
        "extra_metadata": log.extra_metadata,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    })
