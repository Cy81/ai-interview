from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from .base import BaseModel


class QuestionBank(BaseModel):
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), nullable=False, comment="分类: 技术基础/编程能力/项目经验/系统设计/行为面试")
    position_tag = Column(String(100), nullable=True, comment="岗位标签")
    difficulty = Column(String(20), default="medium", comment="难度: easy/medium/hard")
    question = Column(Text, nullable=False, comment="题面")
    reference_answer = Column(Text, nullable=True, comment="参考答案")
    key_points = Column(JSONB, nullable=True, comment="答题要点列表")
    tags = Column(JSONB, nullable=True, comment="标签列表")
    is_vectorized = Column(Boolean, default=False, comment="是否已向量化")
    embedding = Column(Vector(1024), nullable=True, comment="向量嵌入")
    usage_count = Column(Integer, default=0, comment="使用次数")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
