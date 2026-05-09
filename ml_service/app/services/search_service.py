import json
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from ml_service.app.services.embedding_service import EmbeddingService
from ml_service.app.services.faiss_index import FaissIndex


class SearchService:
    def __init__(self, models_dir: Path, embedding_service: EmbeddingService):
        search_dir = models_dir / "relevant_search"

        with open(search_dir / "search_hybrid_config.json", "r", encoding="utf-8") as f:
            self._config = json.load(f)

        with open(search_dir / "search_bm25.pkl", "rb") as f:
            self._bm25 = pickle.load(f)

        self._embeddings = np.load(search_dir / "search_sbert_embeddings.npy")
        self._metadata = pd.read_csv(search_dir / "search_metadata.csv")
        self._embedding_service = embedding_service
        self._faiss_index = FaissIndex(self._embeddings)

    @staticmethod
    def _clean_text(text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"<.*?>", " ", text)
        text = re.sub(r"http\S+|www\S+", " URL ", text)
        text = re.sub(r"@\w+", " USERNAME ", text)
        text = re.sub(r"\+?\d[\d\-\(\) ]{7,}\d", " PHONE ", text)
        text = re.sub(r"[^а-яa-z0-9ё\s\-\+/#]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _normalize(scores: np.ndarray) -> np.ndarray:
        arr = scores.reshape(-1, 1)
        if np.max(arr) == np.min(arr):
            return np.zeros(len(scores))
        return MinMaxScaler().fit_transform(arr).flatten()

    def search(
        self,
        entity_type: str,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        alpha = self._config["alpha"]
        query_clean = self._clean_text(query)

        bm25_norm = self._normalize(
            self._bm25.get_scores(query_clean.split())
        )

        query_emb = self._embedding_service.encode(query_clean)
        sbert_norm = self._normalize(self._faiss_index.search_all(query_emb))

        final_scores = alpha * bm25_norm + (1 - alpha) * sbert_norm
        top_indices = np.argsort(final_scores)[::-1][:top_k]

        results = []
        for rank_i, idx in enumerate(top_indices):
            row = self._metadata.iloc[idx]
            results.append({
                "id": str(row["id"]),
                "score": round(float(final_scores[idx]), 4),
                "title": str(row.get("title", "")),
                "metadata": {"label": str(row.get("label", "")), "rank": rank_i + 1},
            })
        return results

    def rerank(self, query: str, items: List[dict], top_k: int = 10) -> List[dict]:
        query_emb = self._embedding_service.encode(self._clean_text(query))
        texts = [EmbeddingService.item_to_text(item) for item in items]
        item_embs = self._embedding_service.encode_batch(texts)
        scores = np.dot(item_embs, query_emb)

        scored = sorted(
            [
                {
                    "id": item["id"],
                    "score": round(float(score), 4),
                    "title": item.get("title"),
                    "metadata": item.get("metadata", {}),
                }
                for item, score in zip(items, scores)
            ],
            key=lambda x: x["score"],
            reverse=True,
        )
        return scored[:top_k]
