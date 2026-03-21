from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


EntityType = Literal["job", "resume", "announcement", "project"]
DecisionType = Literal["allow", "review", "reject"]


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    models_loaded: bool
    index_available: bool
    indexed_entities: Dict[str, int]


class IndexedItem(BaseModel):
    id: str = Field(..., description="Уникальный ID сущности")
    title: str = Field(default="", description="Заголовок")
    description: str = Field(default="", description="Основной текст")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndexUpsertRequest(BaseModel):
    entity_type: EntityType
    items: List[IndexedItem]


class IndexDeleteRequest(BaseModel):
    entity_type: EntityType
    ids: List[str]


class IndexStatsResponse(BaseModel):
    entities: Dict[str, int]


class ScoredResult(BaseModel):
    id: str
    score: float
    title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    entity_type: EntityType
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    results: List[ScoredResult]


class RerankItem(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RerankRequest(BaseModel):
    query: str
    items: List[RerankItem]
    top_k: int = Field(default=10, ge=1, le=100)


class RecommendSimilarRequest(BaseModel):
    entity_type: EntityType
    item_id: Optional[str] = None
    item: Optional[IndexedItem] = None
    top_k: int = Field(default=5, ge=1, le=50)
    filters: Dict[str, Any] = Field(default_factory=dict)


class RecommendMatchRequest(BaseModel):
    source_entity_type: EntityType
    target_entity_type: EntityType
    item: IndexedItem
    top_k: int = Field(default=10, ge=1, le=100)
    filters: Dict[str, Any] = Field(default_factory=dict)


class RecommendResponse(BaseModel):
    results: List[ScoredResult]


class ModerationRequest(BaseModel):
    content_type: EntityType
    title: str = ""
    description: str = ""
    author_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModerationResponse(BaseModel):
    decision: DecisionType
    risk_score: float
    labels: Dict[str, float]
    reasons: List[str]
