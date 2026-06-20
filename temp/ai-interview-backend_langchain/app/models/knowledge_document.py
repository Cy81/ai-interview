from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .base import BaseModel


class KnowledgeDocument(BaseModel):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, comment="文档标题")
    filename = Column(String(255), nullable=False, comment="原始文件名")
    doc_type = Column(String(50), nullable=False, comment="文档类型: pdf/docx/txt/md")
    category = Column(String(100), nullable=True, comment="分类")
    description = Column(Text, nullable=True, comment="简介")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, default=0, comment="文件大小(字节)")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    is_vectorized = Column(Boolean, default=False, comment="是否已向量化")
    is_enabled = Column(Boolean, default=True, comment="是否启用")

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="KnowledgeChunk.chunk_index"
    )


class KnowledgeChunk(BaseModel):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index = Column(Integer, nullable=False, comment="分块序号")
    content = Column(Text, nullable=False, comment="分块内容")
    is_vectorized = Column(Boolean, default=False, comment="是否已向量化")
    embedding = Column(Vector(1024), nullable=True, comment="向量嵌入")

    document = relationship("KnowledgeDocument", back_populates="chunks")
