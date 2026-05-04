import json
import numpy as np
import pandas as pd
import math

loaded_geo_embeddings = np.load("recommend_sbert_geo_embeddings.npy")
loaded_geo_metadata = pd.read_csv("recommend_sbert_geo_metadata.csv")

with open("recommend_sbert_geo_config.json", "r", encoding="utf-8") as f:
    loaded_geo_config = json.load(f)

loaded_geo_id_to_idx = {
    str(v): i for i, v in enumerate(loaded_geo_metadata["id"].astype(str))
}

def loaded_haversine_km(lat1, lon1, lat2, lon2):
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return np.nan
    
    R = 6371.0
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def loaded_geo_bonus_by_distance(distance_km, max_bonus=0.08):
    if pd.isna(distance_km):
        return 0.0
    
    if distance_km <= 10:
        return max_bonus
    elif distance_km <= 50:
        return max_bonus * 0.7
    elif distance_km <= 100:
        return max_bonus * 0.4
    elif distance_km <= 250:
        return max_bonus * 0.15
    else:
        return 0.0
    
def loaded_recommend_sbert_geo_rerank(vacancy_id, top_k=5):
    idx = loaded_geo_id_to_idx[str(vacancy_id)]
    
    candidate_k = loaded_geo_config["candidate_k"]
    label_bonus = loaded_geo_config["label_bonus"]
    max_geo_bonus = loaded_geo_config["max_geo_bonus"]
    
    semantic_scores = np.dot(loaded_geo_embeddings, loaded_geo_embeddings[idx])
    semantic_scores[idx] = -1
    
    candidate_indices = np.argsort(semantic_scores)[::-1][:candidate_k]
    
    source = loaded_geo_metadata.iloc[idx]
    source_label = source["label"]
    source_lat = source["lat"]
    source_lon = source["lon"]
    
    reranked = []
    
    for cand_idx in candidate_indices:
        candidate = loaded_geo_metadata.iloc[cand_idx]
        
        semantic_score = float(semantic_scores[cand_idx])
        label_score = label_bonus if candidate["label"] == source_label else 0.0
        
        distance_km = loaded_haversine_km(
            source_lat,
            source_lon,
            candidate["lat"],
            candidate["lon"]
        )
        
        geo_score = loaded_geo_bonus_by_distance(distance_km, max_bonus=max_geo_bonus)
        final_score = semantic_score + label_score + geo_score
        
        reranked.append({
            "idx": cand_idx,
            "semantic_score": semantic_score,
            "label_score": label_score,
            "distance_km": distance_km,
            "geo_score": geo_score,
            "final_score": final_score
        })
    
    reranked = sorted(reranked, key=lambda x: x["final_score"], reverse=True)
    top_items = reranked[:top_k]
    top_indices = [x["idx"] for x in top_items]
    
    result = loaded_geo_metadata.iloc[top_indices][["id", "title", "label", "city", "region"]].copy()

    result["semantic_score"] = [x["semantic_score"] for x in top_items]
    result["label_score"] = [x["label_score"] for x in top_items]
    result["distance_km"] = [x["distance_km"] for x in top_items]
    result["geo_score"] = [x["geo_score"] for x in top_items]
    result["final_score"] = [x["final_score"] for x in top_items]
    result.insert(0, "rank", range(1, len(result) + 1))
    
    return result

geo_sample = loaded_geo_metadata[
    loaded_geo_metadata[["lat", "lon"]].notna().all(axis=1)
].iloc[0]["id"]

print("Source vacancy:")
print(loaded_geo_metadata[loaded_geo_metadata["id"] == geo_sample][["id", "title", "label", "city", "region", "lat", "lon"]])

print("Recommendations:")
loaded_recommend_sbert_geo_rerank(geo_sample, top_k=5)