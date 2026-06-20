from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel


class LLMCallLog(BaseModel):
    __tablename__ = "llm_call_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=True, index=True)
    call_type = Column(String(50), nullable=False, index=True)
    question_index = Column(Integer, nullable=True)
    model_name = Column(String(200), nullable=False, index=True)
    temperature = Column(Float, nullable=False)

    # 请求
    request_messages = Column(JSONB, nullable=False)

    # 响应
    response_content = Column(Text, nullable=True)

    # Token 用量
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # 性能
    latency_ms = Column(Integer, nullable=False)

    # 状态
    status = Column(String(20), default="success")  # success / error
    error_message = Column(Text, nullable=True)

    # 扩展
    extra_metadata = Column(JSONB, nullable=True)
