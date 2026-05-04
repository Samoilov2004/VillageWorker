import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ml_service.app.services.embedding_service import EmbeddingService


class RecommendationService:
    def __init__(self, models_dir: Path, embedding_service: EmbeddingService):
        rec_dir = models_dir / "vacancy_recomendation"

        self._embeddings = np.load(rec_dir / "recommend_sbert_geo_embeddings.npy")
        self._metadata = pd.read_csv(rec_dir / "recommend_sbert_geo_metadata.csv")
        with open(rec_dir / "recommend_sbert_geo_config.json", "r", encoding="utf-8") as f:
            self._config = json.load(f)

        self._id_to_idx: Dict[str, int] = {
            str(v): i for i, v in enumerate(self._metadata["id"].astype(str))
        }
        self._embedding_service = embedding_service

    @staticmethod
    def _haversine_km(lat1, lon1, lat2, lon2) -> float:
        if any(pd.isna(v) for v in [lat1, lon1, lat2, lon2]):
            return float("nan")
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)
        a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _geo_bonus(distance_km: float, max_bonus: float) -> float:
        if math.isnan(distance_km):
            return 0.0
        if distance_km <= 10:
            return max_bonus
        elif distance_km <= 50:
            return max_bonus * 0.7
        elif distance_km <= 100:
            return max_bonus * 0.4
        elif distance_km <= 250:
            return max_bonus * 0.15
        return 0.0

    def _rerank_candidates(
        self,
        source_idx: int,
        source_emb: np.ndarray,
        source_label: str,
        source_lat,
        source_lon,
        top_k: int,
    ) -> List[dict]:
        candidate_k = self._config["candidate_k"]
        label_bonus = self._config["label_bonus"]
        max_geo_bonus = self._config["max_geo_bonus"]

        semantic_scores = np.dot(self._embeddings, source_emb)
        if source_idx >= 0:
            semantic_scores[source_idx] = -1.0

        candidate_indices = np.argsort(semantic_scores)[::-1][:candidate_k]

        reranked = []
        for cand_idx in candidate_indices:
            cand = self._metadata.iloc[cand_idx]
            sem = float(semantic_scores[cand_idx])
            lbl = label_bonus if str(cand.get("label", "")) == source_label else 0.0
            dist = self._haversine_km(source_lat, source_lon, cand.get("lat"), cand.get("lon"))
            geo = self._geo_bonus(dist, max_geo_bonus)
            reranked.append({"idx": int(cand_idx), "final_score": sem + lbl + geo})

        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked[:top_k]

    def _row_to_result(self, row, score: float) -> dict:
        return {
            "id": str(row["id"]),
            "score": round(score, 4),
            "title": str(row.get("title", "")),
            "metadata": {
                "label": str(row.get("label", "")),
                "city": str(row.get("city", "")),
                "region": str(row.get("region", "")),
            },
        }

    def similar(
        self,
        entity_type: str,
        top_k: int = 5,
        item_id: Optional[str] = None,
        item: Optional[dict] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        if item_id is not None:
            idx = self._id_to_idx.get(str(item_id))
            if idx is None:
                raise ValueError(f"Vacancy '{item_id}' not found in recommendation index")
            source_emb = self._embeddings[idx]
            row = self._metadata.iloc[idx]
            source_label = str(row.get("label", ""))
            source_lat, source_lon = row.get("lat"), row.get("lon")
            source_idx = idx
        elif item is not None:
            source_emb = self._embedding_service.encode(EmbeddingService.item_to_text(item))
            meta = item.get("metadata", {})
            source_label = str(meta.get("label", ""))
            source_lat, source_lon = meta.get("lat"), meta.get("lon")
            source_idx = -1
        else:
            raise ValueError("Either item_id or item must be provided")

        top_items = self._rerank_candidates(source_idx, source_emb, source_label, source_lat, source_lon, top_k)
        return [self._row_to_result(self._metadata.iloc[e["idx"]], e["final_score"]) for e in top_items]

    def match(
        self,
        source_item: dict,
        target_entity_type: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        source_emb = self._embedding_service.encode(EmbeddingService.item_to_text(source_item))
        meta = source_item.get("metadata", {})
        source_label = str(meta.get("label", ""))
        source_lat, source_lon = meta.get("lat"), meta.get("lon")

        top_items = self._rerank_candidates(-1, source_emb, source_label, source_lat, source_lon, top_k)
        return [self._row_to_result(self._metadata.iloc[e["idx"]], e["final_score"]) for e in top_items]
