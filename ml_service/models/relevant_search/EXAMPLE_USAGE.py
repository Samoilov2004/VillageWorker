import json
import re
import pickle
from rank_bm25 import BM25Okapi
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sentence_transformers import SentenceTransformer
import pandas as pd

import warnings

warnings.filterwarnings("ignore")

with open("search_hybrid_config.json", "r", encoding="utf-8") as f:
    loaded_hybrid_config = json.load(f)

with open("search_bm25.pkl", "rb") as f:
    loaded_bm25 = pickle.load(f)

with open("search_sbert_config.json", "r", encoding="utf-8") as f:
    loaded_sbert_config = json.load(f)

loaded_sbert_model = SentenceTransformer(loaded_sbert_config["sbert_model_name"])

loaded_sbert_embeddings = np.load("search_sbert_embeddings.npy")

loaded_metadata = pd.read_csv("search_metadata.csv")

def tokenize(text):
    return clean_text(text).split()

def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"http\S+|www\S+", " URL ", text)
    text = re.sub(r"@\w+", " USERNAME ", text)
    text = re.sub(r"\+?\d[\d\-\(\) ]{7,}\d", " PHONE ", text)
    text = re.sub(r"[^а-яa-z0-9ё\s\-\+/#]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def loaded_normalize_scores(scores):
    scores = np.array(scores).reshape(-1, 1)
    
    if np.max(scores) == np.min(scores):
        return np.zeros(len(scores))
    
    scaler = MinMaxScaler()
    return scaler.fit_transform(scores).flatten()

def loaded_search_hybrid(query, top_k=5):
    alpha = loaded_hybrid_config["alpha"]
    query_clean = clean_text(query)
    
    bm25_scores = loaded_bm25.get_scores(tokenize(query_clean))
    bm25_scores_norm = loaded_normalize_scores(bm25_scores)
    
    query_emb = loaded_sbert_model.encode(
        [query_clean],
        normalize_embeddings=True
    )[0]

    sbert_scores = np.dot(loaded_sbert_embeddings, query_emb)
    sbert_scores_norm = loaded_normalize_scores(sbert_scores)
    
    final_scores = alpha * bm25_scores_norm + (1 - alpha) * sbert_scores_norm
    
    top_indices = np.argsort(final_scores)[::-1][:top_k]
    
    result = loaded_metadata.iloc[top_indices][["id", "title", "label"]].copy()
    result["bm25_score"] = bm25_scores_norm[top_indices]
    result["sbert_score"] = sbert_scores_norm[top_indices]
    result["final_score"] = final_scores[top_indices]
    result.insert(0, "rank", range(1, len(result) + 1))
    
    return result

print(loaded_search_hybrid("продавец собак", top_k=5))