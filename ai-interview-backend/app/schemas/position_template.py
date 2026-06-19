from typing import Optional, List
from datetime import datetime
from .base import BaseSchema


class PositionTemplateCreate(BaseSchema):
    position_tag: str
    title: str
    category: Optional[str] = None
    level: str = "mid"
    description: Optional[str] = None
    core_skills: Optional[List[str]] = None
    interview_focus: Optional[str] = None
    recommended_difficulty: str = "medium"
    recommended_questions: int = 5
    key_evaluation_criteria: Optional[str] = None


class PositionTemplateUpdate(BaseSchema):
    position_tag: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    description: Optional[str] = None
    core_skills: Optional[List[str]] = None
    interview_focus: Optional[str] = None
    recommended_difficulty: Optional[str] = None
    recommended_questions: Optional[int] = None
    key_evaluation_criteria: Optional[str] = None


class PositionTemplateToggle(BaseSchema):
    is_enabled: bool


class PositionTemplateResponse(BaseSchema):
    id: int
    position_tag: str
    title: str
    category: Optional[str] = None
    level: str
    description: Optional[str] = None
    core_skills: Optional[List[str]] = None
    interview_focus: Optional[str] = None
    recommended_difficulty: str
    recommended_questions: int
    key_evaluation_criteria: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
