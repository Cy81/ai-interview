from .base import BaseSchema
from typing import Optional, List, Any
from datetime import datetime


class LLMLogResponse(BaseSchema):
    id: int
    interview_id: Optional[int] = None
    call_type: str
    question_index: Optional[int] = None
    model_name: str
    temperature: float
    response_content: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime


class LLMLogDetailResponse(LLMLogResponse):
    request_messages: List[Any] = []
    extra_metadata: Optional[Any] = None


class TokenStatsResponse(BaseSchema):
    total_tokens: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_calls: int = 0
    avg_latency_ms: int = 0
    by_model: List[dict] = []
    by_call_type: List[dict] = []
    daily_breakdown: List[dict] = []


class CostEstimateResponse(BaseSchema):
    total_cost: float = 0.0
    by_model: List[dict] = []


class EvaluationMetricsResponse(BaseSchema):
    avg_score: float = 0.0
    total_evaluations: int = 0
    score_distribution: dict = {}
    evaluations_by_model: List[dict] = []
