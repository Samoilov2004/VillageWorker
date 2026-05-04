import re
from typing import Dict

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self._model = SentenceTransformer(model_name)

    def encode(self, text: str) -> np.ndarray:
        return self._model.encode([text], normalize_embeddings=True)[0]

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(texts, normalize_embeddings=True)

    @staticmethod
    def item_to_text(item: Dict) -> str:
        parts = [item.get("title", ""), item.get("description", "")]
        for v in item.get("metadata", {}).values():
            if isinstance(v, (str, int, float)):
                parts.append(str(v))
        return " ".join(p for p in parts if p).strip()
