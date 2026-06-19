from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel


class PositionTemplate(BaseModel):
    __tablename__ = "position_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    position_tag = Column(String(100), nullable=False, comment="岗位标签")
    title = Column(String(255), nullable=False, comment="标题")
    category = Column(String(100), nullable=True, comment="分类")
    level = Column(String(20), default="mid", comment="级别: junior/mid/senior/lead")
    description = Column(Text, nullable=True, comment="描述")
    core_skills = Column(JSONB, nullable=True, comment="核心技能列表")
    interview_focus = Column(Text, nullable=True, comment="面试重点")
    recommended_difficulty = Column(String(20), default="medium", comment="推荐难度")
    recommended_questions = Column(Integer, default=5, comment="推荐题数")
    key_evaluation_criteria = Column(Text, nullable=True, comment="评估标准")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
