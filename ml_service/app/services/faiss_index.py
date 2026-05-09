import numpy as np
import faiss


class FaissIndex:
    """
    Exact inner-product index backed by FAISS IndexFlatIP.

    For unit-normalised embeddings inner product == cosine similarity.
    To migrate to approximate search on larger datasets (100k+), swap
    IndexFlatIP for IndexIVFFlat / IndexHNSWFlat — the public API is identical.
    """

    def __init__(self, embeddings: np.ndarray) -> None:
        vecs = np.ascontiguousarray(embeddings, dtype=np.float32)
        self._n, dim = vecs.shape
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(vecs)

    @property
    def n(self) -> int:
        return self._n

    def search_all(self, query: np.ndarray) -> np.ndarray:
        """
        Return a float64 score array of length N in original index order.

        Equivalent to np.dot(matrix, query) but runs through FAISS BLAS
        kernels. The result is identical — use this when all N scores are
        needed (e.g. for hybrid BM25 + SBERT normalization).
        """
        q = np.ascontiguousarray(query, dtype=np.float32).reshape(1, -1)
        scores, indices = self._index.search(q, self._n)
        out = np.empty(self._n, dtype=np.float64)
        out[indices[0]] = scores[0].astype(np.float64)
        return out

    def search_top_k(
        self, query: np.ndarray, k: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Return (scores, indices) for the top-k most similar vectors.

        Uses FAISS heap selection: avoids a full O(N log N) sort — only the
        top-k heap is maintained while scanning N vectors in O(N + k log k).
        Prefer this over search_all when k << N.
        """
        k = min(k, self._n)
        q = np.ascontiguousarray(query, dtype=np.float32).reshape(1, -1)
        scores, indices = self._index.search(q, k)
        return scores[0].astype(np.float64), indices[0]
