from typing import Any, Dict, List

from ml_service.app.services.embedding_service import EmbeddingService
from ml_service.app.services.index_store import IndexStore


class SearchService:
    def __init__(self, store: IndexStore, embedding_service: EmbeddingService):
        self.store = store
        self.embedding_service = embedding_service

    def _matches_filters(self, item: dict, filters: Dict[str, Any]) -> bool:
        if not filters:
            return True

        metadata = item.get("metadata", {})
        for key, expected_value in filters.items():
            actual_value = metadata.get(key)
            if actual_value != expected_value:
                return False
        return True

    def search(self, entity_type: str, query: str, top_k: int = 10, filters: Dict[str, Any] | None = None) -> List[dict]:
        filters = filters or {}
        items = self.store.list_items(entity_type)

        scored = []
        for item in items:
            if not self._matches_filters(item, filters):
                continue

            item_text = self.embedding_service.item_to_text(item)
            score = self.embedding_service.cosine_similarity(query, item_text)

            if score > 0:
                scored.append({
                    "id": item["id"],
                    "score": round(score, 4),
                    "title": item.get("title"),
                    "metadata": item.get("metadata", {})
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def rerank(self, query: str, items: List[dict], top_k: int = 10) -> List[dict]:
        scored = []
        for item in items:
            item_text = self.embedding_service.item_to_text(item)
            score = self.embedding_service.cosine_similarity(query, item_text)
            scored.append({
                "id": item["id"],
                "score": round(score, 4),
                "title": item.get("title"),
                "metadata": item.get("metadata", {})
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
