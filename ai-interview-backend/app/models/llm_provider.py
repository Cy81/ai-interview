from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class LLMProvider(BaseModel):
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment="提供商名称：DeepSeek、OpenAI 等")
    base_url = Column(String(500), nullable=False, comment="API 基础 URL")
    api_key = Column(String(500), nullable=False, comment="API 密钥")
    is_enabled = Column(Boolean, default=True, comment="是否启用")

    models = relationship(
        "LLMModel",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class LLMModel(BaseModel):
    __tablename__ = "llm_models"
    __table_args__ = (
        UniqueConstraint("provider_id", "model_name", name="uq_provider_model"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_id = Column(
        Integer,
        ForeignKey("llm_providers.id", ondelete="CASCADE"),
        nullable=False
    )
    model_name = Column(String(200), nullable=False, comment="模型标识：deepseek-chat、gpt-4o")
    display_name = Column(String(200), nullable=False, comment="显示名称：DeepSeek V3、GPT-4o")
    is_active = Column(Boolean, default=False, comment="是否为当前激活的模型")

    provider = relationship("LLMProvider", back_populates="models")
