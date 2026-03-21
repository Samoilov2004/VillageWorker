from typing import Any, Dict, List, Optional

from ml_service.app.services.embedding_service import EmbeddingService
from ml_service.app.services.index_store import IndexStore


class RecommendationService:
    def __init__(self, store: IndexStore, embedding_service: EmbeddingService):
        self.store = store
        self.embedding_service = embedding_service

    def _matches_filters(self, item: dict, filters: Dict[str, Any]) -> bool:
        if not filters:
            return True

        metadata = item.get("metadata", {})
        for key, expected_value in filters.items():
            if metadata.get(key) != expected_value:
                return False
        return True

    def _score_against_collection(
        self,
        source_item: dict,
        target_items: List[dict],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[dict]:
        filters = filters or {}
        source_text = self.embedding_service.item_to_text(source_item)

        scored = []
        for item in target_items:
            if item["id"] == source_item.get("id"):
                continue

            if not self._matches_filters(item, filters):
                continue

            target_text = self.embedding_service.item_to_text(item)
            score = self.embedding_service.cosine_similarity(source_text, target_text)

            if score > 0:
                scored.append({
                    "id": item["id"],
                    "score": round(score, 4),
                    "title": item.get("title"),
                    "metadata": item.get("metadata", {})
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def similar(
        self,
        entity_type: str,
        top_k: int = 5,
        item_id: str | None = None,
        item: dict | None = None,
        filters: Dict[str, Any] | None = None,
    ) -> List[dict]:
        if item_id:
            source_item = self.store.get(entity_type, item_id)
            if not source_item:
                raise ValueError(f"Item '{item_id}' not found in index '{entity_type}'")
        elif item:
            source_item = item
        else:
            raise ValueError("Either item_id or item must be provided")

        target_items = self.store.list_items(entity_type)
        return self._score_against_collection(source_item, target_items, top_k, filters)

    def match(
        self,
        source_item: dict,
        target_entity_type: str,
        top_k: int = 10,
        filters: Dict[str, Any] | None = None,
    ) -> List[dict]:
        target_items = self.store.list_items(target_entity_type)
        return self._score_against_collection(source_item, target_items, top_k, filters)
