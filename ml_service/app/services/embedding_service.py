import math
import re
from collections import Counter
from typing import Dict


class EmbeddingService:
    """
    Временная заглушка вместо настоящих embeddings.
    Потом поменяю на sentence-transformers / faiss / или хз
    """

    token_pattern = re.compile(r"[A-Za-zА-Яа-я0-9_]+")

    def normalize_text(self, text: str) -> str:
        return (text or "").lower().strip()

    def tokenize(self, text: str) -> list[str]:
        text = self.normalize_text(text)
        return self.token_pattern.findall(text)

    def vectorize(self, text: str) -> Counter:
        return Counter(self.tokenize(text))

    def cosine_similarity(self, text_a: str, text_b: str) -> float:
        vec_a = self.vectorize(text_a)
        vec_b = self.vectorize(text_b)

        if not vec_a or not vec_b:
            return 0.0

        common = set(vec_a) & set(vec_b)
        dot = sum(vec_a[token] * vec_b[token] for token in common)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def item_to_text(self, item: Dict) -> str:
        title = item.get("title", "")
        description = item.get("description", "")
        metadata = item.get("metadata", {})

        meta_parts = []
        for key, value in metadata.items():
            if isinstance(value, (str, int, float)):
                meta_parts.append(f"{key} {value}")

        return " ".join([title, description, " ".join(meta_parts)]).strip()
