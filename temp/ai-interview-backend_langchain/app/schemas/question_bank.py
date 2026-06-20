from typing import Optional, List
from datetime import datetime
from .base import BaseSchema


class QuestionBankCreate(BaseSchema):
    category: str
    position_tag: Optional[str] = None
    difficulty: str = "medium"
    question: str
    reference_answer: Optional[str] = None
    key_points: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class QuestionBankUpdate(BaseSchema):
    category: Optional[str] = None
    position_tag: Optional[str] = None
    difficulty: Optional[str] = None
    question: Optional[str] = None
    reference_answer: Optional[str] = None
    key_points: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class QuestionBankToggle(BaseSchema):
    is_enabled: bool


class QuestionBankResponse(BaseSchema):
    id: int
    category: str
    position_tag: Optional[str] = None
    difficulty: str
    question: str
    reference_answer: Optional[str] = None
    key_points: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_vectorized: bool
    usage_count: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class QuestionBankBatchImport(BaseSchema):
    questions: List[QuestionBankCreate]


class QuestionBankTestRetrieve(BaseSchema):
    query: str
    top_k: int = 5
    position_tag: Optional[str] = None
    difficulty: Optional[str] = None
    min_score: Optional[float] = None


class QuestionBankStats(BaseSchema):
    total: int
    vectorized: int
    categories: int
    max_usage: int


class QuestionBankRetrieveResult(BaseSchema):
    similarity_score: float
    question_id: int
    question: str
    category: str
    difficulty: str
    position_tag: Optional[str] = None
    reference_answer: Optional[str] = None
