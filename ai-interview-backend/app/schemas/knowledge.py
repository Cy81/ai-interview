from typing import Optional, List
from datetime import datetime
from .base import BaseSchema


class KnowledgeDocumentResponse(BaseSchema):
    id: int
    title: str
    filename: str
    doc_type: str
    category: Optional[str] = None
    description: Optional[str] = None
    file_size: int
    chunk_count: int
    is_vectorized: bool
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentToggle(BaseSchema):
    is_enabled: bool


class KnowledgeChunkResponse(BaseSchema):
    id: int
    document_id: int
    chunk_index: int
    content: str
    is_vectorized: bool
    created_at: datetime
    updated_at: datetime


class KnowledgeTestRetrieve(BaseSchema):
    query: str
    top_k: int = 5
    category: Optional[str] = None


class KnowledgeRetrieveResult(BaseSchema):
    similarity_score: float
    chunk_content: str
    document_id: int
    document_title: str
    chunk_index: int
